"""Read QGIS Server project files and extract publishable layers."""

from pathlib import Path
from xml.etree import ElementTree
import logging

from mviewer.utils import normalize_xml_id
from qgisxmviewer.exceptions import QgisProjectError
from qgisxmviewer.models import QgisExtent, QgisLayer
from qgisxmviewer.utils import parse_qgis_datasource, validate_project_path

LOGGER = logging.getLogger(__name__)


def read_qgis_server_project(project_path: Path) -> list[QgisLayer]:
    """Read a QGIS Server project and return its published layers.

    Args:
        project_path: Path to the QGIS ``.qgs`` XML project.

    Returns:
        Layers extracted from the QGIS project in layer-tree order when
        possible.

    Raises:
        FileNotFoundError: If the project file does not exist.
        QgisProjectError: If the XML cannot be parsed or contains no layers.
    """
    path = validate_project_path(project_path)
    LOGGER.info("Reading QGIS project from %s", path)
    try:
        tree = ElementTree.parse(path)
    except ElementTree.ParseError as exc:
        raise QgisProjectError(f"Invalid QGIS project XML: {path}") from exc

    root = tree.getroot()
    maplayers = root.findall(".//projectlayers/maplayer")
    if not maplayers:
        raise QgisProjectError(f"QGIS project contains no maplayer entries: {path}")

    tree_metadata = _read_layer_tree(root)
    layers_by_id = {
        layer.id: layer
        for layer in (
            _read_maplayer(node, tree_metadata.get(_layer_id(node), {}))
            for node in maplayers
        )
        if layer is not None
    }
    ordered_ids = [layer_id for layer_id in tree_metadata if layer_id in layers_by_id]
    ordered_layers = [layers_by_id[layer_id] for layer_id in ordered_ids]
    ordered_layers.extend(
        layer
        for layer_id, layer in layers_by_id.items()
        if layer_id not in tree_metadata
    )

    if not ordered_layers:
        raise QgisProjectError(f"QGIS project contains no publishable layers: {path}")

    LOGGER.info("Extracted %d QGIS layers", len(ordered_layers))
    return ordered_layers


def _read_maplayer(
    node: ElementTree.Element, tree_info: dict[str, object]
) -> QgisLayer | None:
    """Create a QgisLayer from a QGIS ``maplayer`` node."""
    layer_id = _layer_id(node)
    name = (
        _text(node, "layername")
        or tree_info.get("name")
        or _text(node, "shortname")
        or layer_id
    )
    provider = _text(node, "provider") or _tree_value(tree_info, "provider")
    source = _text(node, "datasource") or _tree_value(tree_info, "source")
    layer_type = _detect_layer_type(node, provider, source)
    published_name = _published_name(node, tree_info, name, layer_type, source)
    metadata = _custom_properties(node)

    if not layer_id or not name:
        LOGGER.warning("Skipping incomplete QGIS maplayer")
        return None

    return QgisLayer(
        id=_xml_layer_id(layer_type, published_name or name or layer_id),
        name=name,
        title=_text(node, "title") or name,
        provider=provider,
        source=source,
        layer_type=layer_type,
        group=(
            tree_info.get("group") if isinstance(tree_info.get("group"), str) else None
        ),
        visible=bool(tree_info.get("visible", True)),
        crs=_read_crs(node),
        abstract=_text(node, "abstract"),
        extent=_read_extent(node),
        published_name=published_name,
        short_name=_text(node, "shortname"),
        queryable=_metadata_bool(metadata, "WMSIdentify", True),
        wms_published=_metadata_bool(metadata, "WMSPublish", True),
        wfs_published=_metadata_bool(metadata, "WFSPublish", layer_type == "wfs"),
        xyz=_is_xyz_layer(provider, source),
        metadata=metadata,
    )


def _read_layer_tree(root: ElementTree.Element) -> dict[str, dict[str, object]]:
    """Return layer-tree metadata keyed by QGIS layer id."""
    layer_tree = root.find(".//layer-tree-group")
    if layer_tree is None:
        return {}
    result: dict[str, dict[str, object]] = {}

    def visit(group_node: ElementTree.Element, group_name: str | None) -> None:
        current_group = group_node.get("name") or group_name
        for child in list(group_node):
            if child.tag == "layer-tree-group":
                visit(child, child.get("name") or current_group)
            elif child.tag == "layer-tree-layer":
                layer_id = child.get("id")
                if layer_id:
                    result[layer_id] = {
                        "group": current_group,
                        "visible": child.get("checked", "Qt::Checked")
                        != "Qt::Unchecked",
                        "name": child.get("name"),
                        "provider": child.get("providerKey"),
                        "source": child.get("source"),
                    }

    visit(layer_tree, None)
    return result


def _detect_layer_type(
    node: ElementTree.Element, provider: str | None, source: str | None
) -> str:
    """Infer the internal layer type from QGIS metadata."""
    type_attr = (node.get("type") or "").lower()
    provider_value = (provider or "").lower()
    source_value = (source or "").lower()
    datasource = parse_qgis_datasource(source)

    if "geojson" in source_value or source_value.endswith(".json"):
        return "geojson"
    if provider_value in {"wms", "wcs"} or "service=wms" in source_value:
        return "wms"
    if provider_value == "wfs" or "service=wfs" in source_value:
        return "wfs"
    if type_attr == "vector":
        if datasource.get("url", "").lower().endswith((".geojson", ".json")):
            return "geojson"
        return "vector"
    if type_attr == "raster":
        return "raster"
    return "unknown"


def _is_xyz_layer(provider: str | None, source: str | None) -> bool:
    """Return whether a QGIS WMS provider layer is actually an XYZ tile source."""
    if (provider or "").lower() != "wms":
        return False
    datasource = parse_qgis_datasource(source)
    return datasource.get("type", "").lower() == "xyz"


def _xml_layer_id(layer_type: str, published_name: str) -> str:
    """Return the mviewer XML id to emit for a layer."""
    if layer_type == "wms":
        return published_name
    return normalize_xml_id(published_name)


def _published_name(
    node: ElementTree.Element,
    tree_info: dict[str, object],
    fallback: str,
    layer_type: str,
    source: str | None,
) -> str:
    """Return the name exposed by QGIS Server when available."""
    if layer_type == "wms":
        source_params = parse_qgis_datasource(source)
        tree_source_params = parse_qgis_datasource(_tree_value(tree_info, "source"))
        return (
            source_params.get("layers") or tree_source_params.get("layers") or fallback
        )
    return (
        _text(node, "shortname")
        or _text(node, "serverProperties/shortName")
        or fallback
    )


def _tree_value(tree_info: dict[str, object], key: str) -> str | None:
    """Return a string value from layer-tree metadata when available."""
    value = tree_info.get(key)
    return value if isinstance(value, str) and value else None


def _read_crs(node: ElementTree.Element) -> str | None:
    """Read the layer CRS auth id."""
    for path in (
        "srs/spatialrefsys/authid",
        "srs/spatialrefsys/description",
        "crs/spatialrefsys/authid",
    ):
        value = _text(node, path)
        if value:
            return value
    return None


def _read_extent(node: ElementTree.Element) -> QgisExtent | None:
    """Read a QGIS layer extent if present."""
    extent = node.find("extent")
    if extent is None:
        return None
    return QgisExtent(
        xmin=_float_text(extent, "xmin"),
        ymin=_float_text(extent, "ymin"),
        xmax=_float_text(extent, "xmax"),
        ymax=_float_text(extent, "ymax"),
    )


def _custom_properties(node: ElementTree.Element) -> dict[str, str]:
    """Extract QGIS custom properties from a maplayer node."""
    properties: dict[str, str] = {}
    for option in node.findall(".//customproperties/Option"):
        key = option.get("name") or option.get("key")
        value = option.get("value")
        if key and value is not None:
            properties[key] = value
        for child in option.findall(".//Option"):
            child_key = child.get("name") or child.get("key")
            child_value = child.get("value")
            if child_key and child_value is not None:
                properties[child_key] = child_value
    for prop in node.findall(".//customproperties/property"):
        key = prop.get("key")
        value = prop.get("value")
        if key and value is not None:
            properties[key] = value
    return properties


def _metadata_bool(metadata: dict[str, str], key_fragment: str, default: bool) -> bool:
    """Read a boolean custom property by loose key matching."""
    for key, value in metadata.items():
        if key_fragment.lower() in key.lower():
            return value.lower() not in {"0", "false", "no", "off"}
    return default


def _layer_id(node: ElementTree.Element) -> str:
    """Return a QGIS layer identifier."""
    return _text(node, "id") or node.get("id") or ""


def _text(node: ElementTree.Element, path: str) -> str | None:
    """Return stripped text for a child path."""
    child = node.find(path)
    if child is None or child.text is None:
        return None
    value = child.text.strip()
    return value or None


def _float_text(node: ElementTree.Element, path: str) -> float | None:
    """Return a float from a child path when it is valid."""
    value = _text(node, path)
    if value is None:
        return None
    try:
        return float(value)
    except ValueError:
        return None
