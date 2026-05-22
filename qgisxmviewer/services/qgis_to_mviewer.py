"""High-level workflow for QGIS project to mviewer XML conversion."""

from pathlib import Path
from xml.etree.ElementTree import Element
import logging

from qgisxmviewer.exceptions import MviewerXmlError
from qgisxmviewer.models import QgisLayer
from qgisxmviewer.writer.mviewer_xml import build_mviewer_xml, write_mviewer_xml
from qgisxmviewer.converters.geojson import qgis_geojson_layer_to_mviewer_xml
from qgisxmviewer.converters.wfs import qgis_wfs_layer_to_mviewer_xml
from qgisxmviewer.converters.wms import qgis_wms_layer_to_mviewer_xml
from qgisxmviewer.qgis_project import read_qgis_server_project
from qgisxmviewer.wms_capabilities import read_wms_capabilities

LOGGER = logging.getLogger(__name__)


def create_mviewer_config_from_qgis_project(
    project_path: Path,
    output_path: Path,
    service_base_url: str,
) -> Path:
    """Create a mviewer XML configuration from a QGIS Server project.

    Args:
        project_path: Path to the QGIS project file.
        output_path: Destination mviewer XML path.
        service_base_url: Base QGIS Server URL used for WMS and WFS requests.

    Returns:
        Path to the generated XML configuration.
    """
    layers = read_qgis_server_project(project_path)
    xml_layers = convert_qgis_layers_to_mviewer_xml(layers, service_base_url)
    tree = build_mviewer_xml(xml_layers)
    result = write_mviewer_xml(tree, output_path)
    LOGGER.info("Generated mviewer XML from %s", project_path)
    return result


def convert_qgis_layers_to_mviewer_xml(
    layers: list[QgisLayer],
    service_base_url: str,
) -> list[Element]:
    """Convert QGIS layer models to mviewer XML layer elements."""
    elements: list[Element] = []
    for layer in layers:
        if layer.layer_type == "geojson":
            elements.append(qgis_geojson_layer_to_mviewer_xml(layer))
        elif layer.layer_type == "wfs" or layer.wfs_published:
            elements.append(qgis_wfs_layer_to_mviewer_xml(layer, service_base_url))
        elif layer.layer_type in {"wms", "vector", "raster", "unknown"} and layer.wms_published:
            elements.append(qgis_wms_layer_to_mviewer_xml(layer, service_base_url))
        else:
            LOGGER.warning("Skipping unsupported or unpublished layer: %s", layer.name)

    if not elements:
        raise MviewerXmlError("No QGIS layer could be converted to mviewer XML")
    return elements


def create_mviewer_config_from_wms_capabilities(
    capabilities_path: Path,
    output_path: Path,
    service_base_url: str | None = None,
) -> Path:
    """Create a mviewer XML configuration from a WMS GetCapabilities file.

    Args:
        capabilities_path: Path to the WMS GetCapabilities XML file.
        output_path: Destination mviewer XML path.
        service_base_url: Optional service URL overriding the advertised URL.

    Returns:
        Path to the generated XML configuration.
    """
    layers, detected_service_url = read_wms_capabilities(capabilities_path)
    xml_layers = convert_qgis_layers_to_mviewer_xml(
        layers,
        service_base_url or detected_service_url,
    )
    tree = build_mviewer_xml(xml_layers)
    result = write_mviewer_xml(tree, output_path)
    LOGGER.info("Generated mviewer XML from WMS capabilities %s", capabilities_path)
    return result
