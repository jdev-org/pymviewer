"""Convert QGIS GeoJSON layers to mviewer XML layer elements."""

from xml.etree.ElementTree import Element

from mviewer.utils import bool_to_xml
from qgisxmviewer.models import QgisLayer
from qgisxmviewer.utils import parse_qgis_datasource


def qgis_geojson_layer_to_mviewer_xml(layer: QgisLayer) -> Element:
    """Convert a QGIS GeoJSON layer to a mviewer XML layer element."""
    datasource = parse_qgis_datasource(layer.source)
    url = datasource.get("url") or layer.source or ""
    return Element(
        "layer",
        {
            "id": layer.id,
            "name": layer.title or layer.name,
            "type": "geojson",
            "url": url,
            "visible": bool_to_xml(layer.visible),
            "queryable": bool_to_xml(layer.queryable),
            "searchable": "false",
            "tiled": "false",
            "group": layer.group or "",
            "theme": layer.theme or "",
        },
    )
