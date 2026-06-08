"""High-level workflow for QGIS project to mviewer XML conversion."""

from pathlib import Path
from xml.etree.ElementTree import Element, ElementTree
import logging

from mviewer.converters.geojson import qgis_geojson_layer_to_mviewer_xml
from mviewer.converters.wfs import qgis_wfs_layer_to_mviewer_xml
from mviewer.converters.wms import qgis_wms_layer_to_mviewer_xml
from mviewer.exceptions import MviewerXmlError
from mviewer.writer.mviewer_xml import (
    build_mviewer_xml,
    serialize_mviewer_xml,
    write_mviewer_xml,
)
from qgisxmviewer.models import QgisLayer
from qgisxmviewer.qgis_project import read_qgis_server_project
from qgisxmviewer.wms_capabilities import read_wms_capabilities

LOGGER = logging.getLogger(__name__)


def _normalized_title(value: str | None) -> str:
    """Return a normalized non-empty title string."""
    return " ".join((value or "").split()).strip()


def _preferred_config_title_from_layers(
    layers: list[QgisLayer], fallback: str = "Projet QGIS"
) -> str:
    """Return the preferred configuration title extracted from QGIS layers."""
    for layer in layers:
        for candidate in (layer.group, layer.title, layer.name):
            normalized_candidate = _normalized_title(candidate)
            if normalized_candidate:
                return normalized_candidate
    return fallback


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
    tree = build_mviewer_tree_from_qgis_project(project_path, service_base_url)
    result = write_mviewer_xml(tree, output_path)
    LOGGER.info("Generated mviewer XML from %s", project_path)
    return result


def build_mviewer_tree_from_qgis_project(
    project_path: Path,
    service_base_url: str,
) -> ElementTree:
    """Build a mviewer XML tree from a QGIS Server project.

    Args:
        project_path: Path to the QGIS project file.
        service_base_url: Base QGIS Server URL used for WMS and WFS requests.

    Returns:
        XML tree ready to serialize or write to disk.
    """
    layers = read_qgis_server_project(project_path)
    xml_layers = convert_qgis_layers_to_mviewer_xml(layers, service_base_url)
    config_title = _preferred_config_title_from_layers(layers)
    return build_mviewer_xml(
        xml_layers,
        application_attributes={"title": config_title},
        default_theme_name=config_title,
    )


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
        elif (
            layer.layer_type in {"wms", "vector", "raster", "unknown"}
            and layer.wms_published
        ):
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
    tree = build_mviewer_tree_from_wms_capabilities(
        capabilities_path,
        service_base_url,
    )
    result = write_mviewer_xml(tree, output_path)
    LOGGER.info("Generated mviewer XML from WMS capabilities %s", capabilities_path)
    return result


def build_mviewer_tree_from_wms_capabilities(
    capabilities_path: Path,
    service_base_url: str | None = None,
) -> ElementTree:
    """Build a mviewer XML tree from a WMS GetCapabilities document.

    Args:
        capabilities_path: Path to the WMS GetCapabilities XML file.
        service_base_url: Optional service URL overriding the advertised URL.

    Returns:
        XML tree ready to serialize or write to disk.
    """
    layers, detected_service_url = read_wms_capabilities(capabilities_path)
    xml_layers = convert_qgis_layers_to_mviewer_xml(
        layers,
        service_base_url or detected_service_url,
    )
    config_title = _preferred_config_title_from_layers(layers)
    return build_mviewer_xml(
        xml_layers,
        application_attributes={"title": config_title},
        default_theme_name=config_title,
    )


def create_mviewer_xml_text_from_qgis_project(
    project_path: Path,
    service_base_url: str,
) -> str:
    """Create a serialized mviewer XML document from a QGIS project."""
    return serialize_mviewer_xml(
        build_mviewer_tree_from_qgis_project(project_path, service_base_url)
    )


def create_mviewer_xml_text_from_wms_capabilities(
    capabilities_path: Path,
    service_base_url: str | None = None,
) -> str:
    """Create a serialized mviewer XML document from WMS capabilities."""
    return serialize_mviewer_xml(
        build_mviewer_tree_from_wms_capabilities(
            capabilities_path,
            service_base_url,
        )
    )
