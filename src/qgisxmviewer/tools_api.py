"""Tool-friendly wrappers exposing pymviewer workflows with serializable data."""

from dataclasses import asdict
from pathlib import Path
from typing import Any

from qgisxmviewer.models import QgisLayer
from qgisxmviewer.qgis_project import read_qgis_server_project
from qgisxmviewer.services.qgis_to_mviewer import (
    create_mviewer_config_from_qgis_project,
    create_mviewer_config_from_wms_capabilities,
    create_mviewer_xml_text_from_qgis_project,
    create_mviewer_xml_text_from_wms_capabilities,
)
from qgisxmviewer.wms_capabilities import read_wms_capabilities


def generate_mviewer_from_qgs_tool(
    project_path: str,
    service_url: str,
    output_path: str | None = None,
) -> dict[str, Any]:
    """Generate mviewer XML from a QGIS project for tool usage.

    Args:
        project_path: Path to a QGIS ``.qgs`` project file.
        service_url: Base QGIS Server URL used for WMS and WFS requests.
        output_path: Optional output path. When omitted, XML is returned inline.

    Returns:
        Serializable result describing either the generated file or XML text.
    """
    normalized_project_path = _require_string(project_path, "project_path")
    normalized_service_url = _require_string(service_url, "service_url")
    if output_path is None:
        xml_text = create_mviewer_xml_text_from_qgis_project(
            Path(normalized_project_path),
            normalized_service_url,
        )
        return {
            "mode": "inline",
            "project_path": normalized_project_path,
            "service_url": normalized_service_url,
            "xml": xml_text,
        }

    normalized_output_path = _require_string(output_path, "output_path")
    result_path = create_mviewer_config_from_qgis_project(
        Path(normalized_project_path),
        Path(normalized_output_path),
        normalized_service_url,
    )
    return {
        "mode": "file",
        "project_path": normalized_project_path,
        "service_url": normalized_service_url,
        "output_path": str(result_path),
    }


def generate_mviewer_from_capabilities_tool(
    capabilities_path: str,
    output_path: str | None = None,
    service_url: str | None = None,
) -> dict[str, Any]:
    """Generate mviewer XML from WMS capabilities for tool usage.

    Args:
        capabilities_path: Path to a WMS GetCapabilities XML file.
        output_path: Optional output path. When omitted, XML is returned inline.
        service_url: Optional service URL overriding the advertised URL.

    Returns:
        Serializable result describing either the generated file or XML text.
    """
    normalized_capabilities_path = _require_string(
        capabilities_path,
        "capabilities_path",
    )
    normalized_service_url = _optional_string(service_url, "service_url")
    if output_path is None:
        xml_text = create_mviewer_xml_text_from_wms_capabilities(
            Path(normalized_capabilities_path),
            normalized_service_url,
        )
        return {
            "mode": "inline",
            "capabilities_path": normalized_capabilities_path,
            "service_url": normalized_service_url,
            "xml": xml_text,
        }

    normalized_output_path = _require_string(output_path, "output_path")
    result_path = create_mviewer_config_from_wms_capabilities(
        Path(normalized_capabilities_path),
        Path(normalized_output_path),
        normalized_service_url,
    )
    return {
        "mode": "file",
        "capabilities_path": normalized_capabilities_path,
        "service_url": normalized_service_url,
        "output_path": str(result_path),
    }


def inspect_qgs_layers_tool(project_path: str) -> dict[str, Any]:
    """Inspect publishable QGIS project layers for tool usage."""
    normalized_project_path = _require_string(project_path, "project_path")
    layers = read_qgis_server_project(Path(normalized_project_path))
    return {
        "project_path": normalized_project_path,
        "layer_count": len(layers),
        "layers": [_serialize_layer(layer) for layer in layers],
    }


def inspect_wms_capabilities_tool(capabilities_path: str) -> dict[str, Any]:
    """Inspect named WMS layers from a GetCapabilities document for tool usage."""
    normalized_capabilities_path = _require_string(
        capabilities_path,
        "capabilities_path",
    )
    layers, service_url = read_wms_capabilities(Path(normalized_capabilities_path))
    return {
        "capabilities_path": normalized_capabilities_path,
        "service_url": service_url,
        "layer_count": len(layers),
        "layers": [_serialize_layer(layer) for layer in layers],
    }


def _serialize_layer(layer: QgisLayer) -> dict[str, Any]:
    """Serialize a QgisLayer dataclass to plain JSON-compatible data."""
    return asdict(layer)


def _optional_string(value: str | None, name: str) -> str | None:
    """Return a stripped string value or ``None`` when omitted."""
    if value is None:
        return None
    return _require_string(value, name)


def _require_string(value: str, name: str) -> str:
    """Validate a required non-empty string argument."""
    normalized = value.strip()
    if not normalized:
        raise ValueError(f"{name} must be a non-empty string")
    return normalized
