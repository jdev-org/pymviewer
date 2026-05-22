"""Convert QGIS layers to mviewer WMS XML layer elements."""

from xml.etree.ElementTree import Element

from qgisxmviewer.models import QgisLayer
from qgisxmviewer.utils import bool_to_xml, clean_service_url, rebase_url


def qgis_wms_layer_to_mviewer_xml(layer: QgisLayer, service_base_url: str) -> Element:
    """Convert a QGIS WMS layer to a mviewer XML layer element."""
    published_name = layer.published_name or layer.short_name or layer.name
    attributes = {
        "id": layer.id,
        "name": layer.title or layer.name,
        "type": "wms",
        "url": clean_service_url(service_base_url),
        "layers": published_name,
        "visible": bool_to_xml(layer.visible),
        "queryable": bool_to_xml(layer.queryable),
        "searchable": "false",
        "tiled": "false",
        "format": "image/png",
        "transparent": "true",
        "infoformat": "text/html",
        "featurecount": "10",
        "group": layer.group or "",
    }
    if layer.legend_url:
        attributes["legendurl"] = rebase_url(layer.legend_url, service_base_url) or layer.legend_url
    if layer.abstract:
        attributes["description"] = layer.abstract
    return Element("layer", {key: value for key, value in attributes.items() if value != ""})
