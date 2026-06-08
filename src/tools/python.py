"""Tool-friendly wrappers exposing pymviewer workflows with serializable data."""

from dataclasses import asdict
from pathlib import Path
from typing import Any
from xml.etree.ElementTree import Element

from mviewer.converters.wfs import qgis_wfs_layer_to_mviewer_xml
from mviewer.converters.wms import qgis_wms_layer_to_mviewer_xml
from qgisxmviewer.models import QgisLayer
from qgisxmviewer.qgis_project import read_qgis_server_project
from qgisxmviewer.services.qgis_to_mviewer import (
    create_mviewer_config_from_qgis_project,
    create_mviewer_config_from_wms_capabilities,
    create_mviewer_xml_text_from_qgis_project,
    create_mviewer_xml_text_from_wms_capabilities,
)
from qgisxmviewer.wms_capabilities import read_wms_capabilities


def create_wms_layer_structure_tool(
    service_url: str,
    layer_id: str | None = None,
    name: str | None = None,
    layer_info: dict[str, Any] | None = None,
    qgis_layer: dict[str, Any] | None = None,
    published_name: str | None = None,
    group: str | None = None,
    visible: bool = False,
    queryable: bool = True,
    legend_url: str | None = None,
    abstract: str | None = None,
    xyz: bool = False,
    source: str | None = None,
) -> dict[str, Any]:
    """Create a serializable mviewer WMS layer structure.

    The layer definition can come from:
    - ``qgis_layer``: a serialized ``QgisLayer`` mapping;
    - ``layer_info``: a plain JSON-compatible mapping;
    - explicit keyword arguments.
    """
    layer = _build_wms_layer(
        layer_id=layer_id,
        name=name,
        published_name=published_name,
        group=group,
        visible=visible,
        queryable=queryable,
        legend_url=legend_url,
        abstract=abstract,
        xyz=xyz,
        source=source,
        layer_info=layer_info,
        qgis_layer=qgis_layer,
    )
    return _serialize_wms_layer_structure(layer, service_url)


def create_wfs_layer_structure_tool(
    service_url: str,
    layer_id: str | None = None,
    name: str | None = None,
    layer_info: dict[str, Any] | None = None,
    qgis_layer: dict[str, Any] | None = None,
    published_name: str | None = None,
    group: str | None = None,
    visible: bool = False,
    queryable: bool = True,
    source: str | None = None,
) -> dict[str, Any]:
    """Create a serializable mviewer WFS layer structure.

    The layer definition can come from:
    - ``qgis_layer``: a serialized ``QgisLayer`` mapping;
    - ``layer_info``: a plain JSON-compatible mapping;
    - explicit keyword arguments.
    """
    layer = _build_wfs_layer(
        layer_id=layer_id,
        name=name,
        published_name=published_name,
        group=group,
        visible=visible,
        queryable=queryable,
        source=source,
        layer_info=layer_info,
        qgis_layer=qgis_layer,
    )
    return _serialize_wfs_layer_structure(layer, service_url)


def generate_mviewer_from_qgs_tool(
    project_path: str,
    service_url: str,
    output_path: str | None = None,
) -> dict[str, Any]:
    """Generate mviewer XML from a QGIS project for tool usage."""
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
    """Generate mviewer XML from WMS capabilities for tool usage."""
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


def _serialize_xml_element(element: Element) -> dict[str, Any]:
    """Serialize an XML element to plain JSON-compatible data."""
    return {
        "tag": element.tag,
        "attributes": dict(element.attrib),
    }


def _serialize_wms_layer_structure(
    layer: QgisLayer, service_url: str
) -> dict[str, Any]:
    """Serialize a WMS ``QgisLayer`` into a tool-friendly structure."""
    element = qgis_wms_layer_to_mviewer_xml(
        layer,
        _require_string(service_url, "service_url"),
    )
    return _serialize_xml_element(element)


def _serialize_wfs_layer_structure(
    layer: QgisLayer, service_url: str
) -> dict[str, Any]:
    """Serialize a WFS ``QgisLayer`` into a tool-friendly structure."""
    element = qgis_wfs_layer_to_mviewer_xml(
        layer,
        _require_string(service_url, "service_url"),
    )
    return _serialize_xml_element(element)


def _build_wms_layer(
    layer_id: str | None,
    name: str | None,
    published_name: str | None,
    group: str | None,
    visible: bool,
    queryable: bool,
    legend_url: str | None,
    abstract: str | None,
    xyz: bool,
    source: str | None,
    layer_info: dict[str, Any] | None,
    qgis_layer: dict[str, Any] | None,
) -> QgisLayer:
    """Build a WMS-capable ``QgisLayer`` from tool inputs."""
    if qgis_layer is not None:
        return _qgis_layer_from_mapping(qgis_layer, default_layer_type="wms")

    info = _resolve_layer_info(layer_info)
    resolved_name = _coalesce_string(name, info.get("name"), info.get("title"))
    resolved_layer_id = _coalesce_string(layer_id, info.get("id"), resolved_name)
    resolved_published_name = _coalesce_string(
        published_name,
        info.get("published_name"),
        info.get("short_name"),
        info.get("name"),
        info.get("title"),
        resolved_name,
    )
    resolved_group = _coalesce_optional_string(group, info.get("group"))
    resolved_source = _coalesce_optional_string(source, info.get("source"))
    resolved_legend_url = _coalesce_optional_string(
        legend_url,
        info.get("legend_url"),
    )
    resolved_abstract = _coalesce_optional_string(abstract, info.get("abstract"))
    resolved_visible = _coalesce_bool(info.get("visible"), visible)
    resolved_queryable = _coalesce_bool(info.get("queryable"), queryable)
    resolved_xyz = _coalesce_bool(info.get("xyz"), xyz)

    return QgisLayer(
        id=_require_string(resolved_layer_id, "layer_id"),
        name=_require_string(resolved_name, "name"),
        title=_require_string(resolved_name, "name"),
        provider="wms",
        source=resolved_source,
        layer_type="wms",
        group=resolved_group,
        visible=resolved_visible,
        crs=_coalesce_optional_string(info.get("crs")),
        abstract=resolved_abstract,
        published_name=_require_string(resolved_published_name, "published_name"),
        short_name=_coalesce_optional_string(info.get("short_name")),
        queryable=resolved_queryable,
        wms_published=_coalesce_bool(info.get("wms_published"), True),
        wfs_published=_coalesce_bool(info.get("wfs_published"), False),
        xyz=resolved_xyz,
        legend_url=resolved_legend_url,
        metadata=_coalesce_mapping(info.get("metadata")),
    )


def _build_wfs_layer(
    layer_id: str | None,
    name: str | None,
    published_name: str | None,
    group: str | None,
    visible: bool,
    queryable: bool,
    source: str | None,
    layer_info: dict[str, Any] | None,
    qgis_layer: dict[str, Any] | None,
) -> QgisLayer:
    """Build a WFS-capable ``QgisLayer`` from tool inputs."""
    if qgis_layer is not None:
        return _qgis_layer_from_mapping(qgis_layer, default_layer_type="wfs")

    info = _resolve_layer_info(layer_info)
    resolved_name = _coalesce_string(name, info.get("name"), info.get("title"))
    resolved_layer_id = _coalesce_string(layer_id, info.get("id"), resolved_name)
    resolved_published_name = _coalesce_string(
        published_name,
        info.get("published_name"),
        info.get("short_name"),
        info.get("name"),
        info.get("title"),
        resolved_name,
    )

    return QgisLayer(
        id=_require_string(resolved_layer_id, "layer_id"),
        name=_require_string(resolved_name, "name"),
        title=_require_string(resolved_name, "name"),
        provider="wfs",
        source=_coalesce_optional_string(source, info.get("source")),
        layer_type="wfs",
        group=_coalesce_optional_string(group, info.get("group")),
        visible=_coalesce_bool(info.get("visible"), visible),
        crs=_coalesce_optional_string(info.get("crs")),
        abstract=_coalesce_optional_string(info.get("abstract")),
        published_name=_require_string(resolved_published_name, "published_name"),
        short_name=_coalesce_optional_string(info.get("short_name")),
        queryable=_coalesce_bool(info.get("queryable"), queryable),
        wms_published=_coalesce_bool(info.get("wms_published"), False),
        wfs_published=_coalesce_bool(info.get("wfs_published"), True),
        xyz=_coalesce_bool(info.get("xyz"), False),
        legend_url=_coalesce_optional_string(info.get("legend_url")),
        metadata=_coalesce_mapping(info.get("metadata")),
    )


def _qgis_layer_from_mapping(
    layer_data: dict[str, Any],
    default_layer_type: str,
) -> QgisLayer:
    """Build a ``QgisLayer`` instance from a serialized mapping."""
    resolved_name = _coalesce_string(layer_data.get("name"), layer_data.get("title"))
    return QgisLayer(
        id=_require_string(layer_data.get("id"), "qgis_layer.id"),
        name=_require_string(resolved_name, "qgis_layer.name"),
        title=_coalesce_optional_string(layer_data.get("title"), resolved_name),
        provider=_coalesce_optional_string(layer_data.get("provider")),
        source=_coalesce_optional_string(layer_data.get("source")),
        layer_type=_coalesce_string(layer_data.get("layer_type"), default_layer_type),
        group=_coalesce_optional_string(layer_data.get("group")),
        visible=_coalesce_bool(layer_data.get("visible"), False),
        crs=_coalesce_optional_string(layer_data.get("crs")),
        abstract=_coalesce_optional_string(layer_data.get("abstract")),
        published_name=_coalesce_optional_string(
            layer_data.get("published_name"),
            layer_data.get("short_name"),
            resolved_name,
        ),
        short_name=_coalesce_optional_string(layer_data.get("short_name")),
        queryable=_coalesce_bool(layer_data.get("queryable"), True),
        wms_published=_coalesce_bool(layer_data.get("wms_published"), True),
        wfs_published=_coalesce_bool(layer_data.get("wfs_published"), False),
        xyz=_coalesce_bool(layer_data.get("xyz"), False),
        legend_url=_coalesce_optional_string(layer_data.get("legend_url")),
        metadata=_coalesce_mapping(layer_data.get("metadata")),
    )


def _resolve_layer_info(layer_info: dict[str, Any] | None) -> dict[str, Any]:
    """Return a normalized layer definition mapping."""
    return layer_info or {}


def _coalesce_string(*values: Any) -> str | None:
    """Return the first non-empty string-like value."""
    for value in values:
        candidate = _coalesce_optional_string(value)
        if candidate is not None:
            return candidate
    return None


def _coalesce_optional_string(*values: Any) -> str | None:
    """Return the first non-empty string-like value or ``None``."""
    for value in values:
        if value is None:
            continue
        if isinstance(value, str):
            normalized = value.strip()
            if normalized:
                return normalized
            continue
        normalized = str(value).strip()
        if normalized:
            return normalized
    return None


def _coalesce_bool(value: Any, default: bool) -> bool:
    """Return a boolean value with a fallback default."""
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {"true", "1", "yes", "on"}:
            return True
        if normalized in {"false", "0", "no", "off"}:
            return False
    return bool(value)


def _coalesce_mapping(value: Any) -> dict[str, str]:
    """Return a string-keyed mapping or an empty mapping."""
    if not isinstance(value, dict):
        return {}
    return {str(key): str(item) for key, item in value.items()}
    return {str(key): str(item) for key, item in value.items()}


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
