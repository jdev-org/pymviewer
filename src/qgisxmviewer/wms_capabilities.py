"""Read WMS GetCapabilities XML documents and extract mviewer-ready layers."""

from pathlib import Path
from xml.etree import ElementTree
import logging

from mviewer.utils import normalize_wms_legend_url
from qgisxmviewer.exceptions import QgisProjectError
from qgisxmviewer.models import QgisExtent, QgisLayer

LOGGER = logging.getLogger(__name__)

WMS_NS = {"wms": "http://www.opengis.net/wms"}
XLINK_HREF = "{http://www.w3.org/1999/xlink}href"


def read_wms_capabilities(capabilities_path: Path) -> tuple[list[QgisLayer], str]:
    """Read a WMS GetCapabilities document and return layers plus service URL.

    Args:
        capabilities_path: Path to a WMS GetCapabilities XML file.

    Returns:
        A tuple containing extracted WMS layers and the detected service URL.

    Raises:
        FileNotFoundError: If the capabilities file does not exist.
        QgisProjectError: If the XML is invalid or contains no named WMS layer.
    """
    path = Path(capabilities_path)
    if not path.exists():
        raise FileNotFoundError(f"WMS capabilities file does not exist: {path}")
    if not path.is_file():
        raise QgisProjectError(f"WMS capabilities path is not a file: {path}")

    LOGGER.info("Reading WMS capabilities from %s", path)
    try:
        root = ElementTree.parse(path).getroot()
    except ElementTree.ParseError as exc:
        raise QgisProjectError(f"Invalid WMS capabilities XML: {path}") from exc

    namespace = _namespace(root)
    service_url = _service_url(root, namespace)
    service_title = _text(root, "Service/Title", namespace) or _text(
        root, "Capability/Layer/Title", namespace
    )
    root_layer = _find(root, "Capability/Layer", namespace)
    if root_layer is None:
        raise QgisProjectError(f"WMS capabilities contains no root layer: {path}")

    layers = []
    for node in root_layer.findall(
        ".//wms:Layer" if namespace else ".//Layer", WMS_NS if namespace else {}
    ):
        layer = _read_named_layer(node, service_title, namespace)
        if layer is not None:
            layers.append(layer)
    if not layers:
        raise QgisProjectError(f"WMS capabilities contains no named layers: {path}")

    LOGGER.info("Extracted %d WMS capabilities layers", len(layers))
    return layers, service_url


def _read_named_layer(
    node: ElementTree.Element,
    service_title: str | None,
    namespace: str | None,
) -> QgisLayer | None:
    """Convert a WMS Layer node into a QgisLayer when it has a Name."""
    name = _text_from(node, "Name", namespace)
    if not name:
        return None
    title = _text_from(node, "Title", namespace) or name
    crs = _first_text_from(node, ("CRS", "SRS"), namespace)
    legend_url = normalize_wms_legend_url(_legend_url(node, namespace))
    return QgisLayer(
        id=name,
        name=name,
        title=title,
        provider="wms",
        source=None,
        layer_type="wms",
        group=service_title or "WMS",
        visible=False,
        crs=crs,
        extent=_extent(node, namespace),
        published_name=name,
        queryable=node.get("queryable") in {"1", "true", "True"},
        wms_published=True,
        legend_url=legend_url,
    )


def _service_url(root: ElementTree.Element, namespace: str | None) -> str:
    """Find the WMS service URL advertised by a capabilities document."""
    for path in (
        "Service/OnlineResource",
        "Capability/Request/GetMap/DCPType/HTTP/Get/OnlineResource",
        "Capability/Request/GetCapabilities/DCPType/HTTP/Get/OnlineResource",
    ):
        node = _find(root, path, namespace)
        if node is not None:
            href = node.get(XLINK_HREF) or node.get("href")
            if href:
                return href.rstrip("?")
    raise QgisProjectError("WMS capabilities does not expose a service URL")


def _legend_url(node: ElementTree.Element, namespace: str | None) -> str | None:
    """Return the first legend URL advertised for a WMS layer."""
    legend_path = "Style/LegendURL/OnlineResource"
    legend = _find_from(node, legend_path, namespace)
    if legend is None:
        return None
    return legend.get(XLINK_HREF) or legend.get("href")


def _extent(node: ElementTree.Element, namespace: str | None) -> QgisExtent | None:
    """Read the EPSG:3857 bounding box when available."""
    boxes = node.findall(
        "wms:BoundingBox" if namespace else "BoundingBox", WMS_NS if namespace else {}
    )
    selected = None
    for box in boxes:
        if box.get("CRS") == "EPSG:3857" or box.get("SRS") == "EPSG:3857":
            selected = box
            break
    if selected is None and boxes:
        selected = boxes[0]
    if selected is None:
        return None
    return QgisExtent(
        xmin=_float_attr(selected, "minx"),
        ymin=_float_attr(selected, "miny"),
        xmax=_float_attr(selected, "maxx"),
        ymax=_float_attr(selected, "maxy"),
    )


def _namespace(root: ElementTree.Element) -> str | None:
    """Return the XML namespace URI used by the root element."""
    if root.tag.startswith("{"):
        return root.tag[1:].split("}", 1)[0]
    return None


def _find(
    root: ElementTree.Element, path: str, namespace: str | None
) -> ElementTree.Element | None:
    """Find a child node with optional WMS namespace handling."""
    if namespace:
        return root.find("/".join(f"wms:{part}" for part in path.split("/")), WMS_NS)
    return root.find(path)


def _find_from(
    node: ElementTree.Element, path: str, namespace: str | None
) -> ElementTree.Element | None:
    """Find a descendant node with optional WMS namespace handling."""
    if namespace:
        return node.find("/".join(f"wms:{part}" for part in path.split("/")), WMS_NS)
    return node.find(path)


def _text(root: ElementTree.Element, path: str, namespace: str | None) -> str | None:
    """Read text from a path relative to the root."""
    node = _find(root, path, namespace)
    if node is None or node.text is None:
        return None
    return node.text.strip() or None


def _text_from(
    node: ElementTree.Element, path: str, namespace: str | None
) -> str | None:
    """Read text from a path relative to a node."""
    child = _find_from(node, path, namespace)
    if child is None or child.text is None:
        return None
    return child.text.strip() or None


def _first_text_from(
    node: ElementTree.Element,
    paths: tuple[str, ...],
    namespace: str | None,
) -> str | None:
    """Return the first non-empty text from candidate paths."""
    for path in paths:
        value = _text_from(node, path, namespace)
        if value:
            return value
    return None


def _float_attr(node: ElementTree.Element, name: str) -> float | None:
    """Read a float attribute when it is present and valid."""
    value = node.get(name)
    if value is None:
        return None
    try:
        return float(value)
    except ValueError:
        return None
