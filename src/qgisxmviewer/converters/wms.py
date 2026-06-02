"""Convert QGIS layers to mviewer WMS XML layer elements."""

from xml.etree.ElementTree import Element

from qgisxmviewer.models import QgisLayer
from qgisxmviewer.utils import (
    bool_to_xml,
    clean_service_url,
    encode_wms_layer_name,
    parse_qgis_datasource,
    rebase_url,
)


def qgis_wms_layer_to_mviewer_xml(layer: QgisLayer, service_base_url: str) -> Element:
    """Convert a QGIS WMS layer to a mviewer XML layer element."""
    published_name = layer.published_name or layer.short_name or layer.name
    encoded_published_name = encode_wms_layer_name(published_name)
    datasource = parse_qgis_datasource(layer.source)
    layer_url = datasource.get("url") if layer.xyz else clean_service_url(service_base_url)
    attributes = {
        "id": layer.id,
        "name": layer.title or layer.name,
        "type": "wms",
        "url": layer_url,
        "layers": None if layer.xyz else encoded_published_name,
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
    if layer.xyz:
        attributes["xyz"] = "true"
    if layer.legend_url:
        attributes["legendurl"] = rebase_url(layer.legend_url, service_base_url) or layer.legend_url
    if layer.abstract:
        attributes["description"] = layer.abstract
    return Element("layer", {key: value for key, value in attributes.items() if value not in {"", None}})
