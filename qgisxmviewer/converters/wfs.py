"""Convert QGIS WFS layers to mviewer GeoJSON XML layer elements."""

from xml.etree.ElementTree import Element

from qgisxmviewer.models import QgisLayer
from qgisxmviewer.utils import add_query_params, bool_to_xml


def qgis_wfs_layer_to_mviewer_xml(layer: QgisLayer, service_base_url: str) -> Element:
    """Convert a QGIS WFS layer to a mviewer XML layer element."""
    typename = layer.published_name or layer.short_name or layer.name
    url = add_query_params(
        service_base_url,
        {
            "SERVICE": "WFS",
            "VERSION": "1.0.0",
            "REQUEST": "GetFeature",
            "TYPENAME": typename,
            "outputFormat": "application/json",
            "srsName": "EPSG:4326",
        },
    )
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
        },
    )
