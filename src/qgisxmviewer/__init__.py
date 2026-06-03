"""QGIS and QGIS Server tools for pymviewer."""

from importlib import import_module
from typing import Any

__all__ = [
    "MviewerLayer",
    "QgisExtent",
    "QgisLayer",
    "build_mviewer_tree_from_qgis_project",
    "build_mviewer_tree_from_wms_capabilities",
    "convert_qgis_layers_to_mviewer_xml",
    "create_mviewer_config_from_qgis_project",
    "create_mviewer_config_from_wms_capabilities",
    "create_mviewer_xml_text_from_qgis_project",
    "create_mviewer_xml_text_from_wms_capabilities",
    "read_qgis_server_project",
    "read_wms_capabilities",
]

_EXPORTS = {
    "MviewerLayer": ("mviewer.models", "MviewerLayer"),
    "QgisExtent": ("qgisxmviewer.models", "QgisExtent"),
    "QgisLayer": ("qgisxmviewer.models", "QgisLayer"),
    "build_mviewer_tree_from_qgis_project": (
        "qgisxmviewer.services.qgis_to_mviewer",
        "build_mviewer_tree_from_qgis_project",
    ),
    "build_mviewer_tree_from_wms_capabilities": (
        "qgisxmviewer.services.qgis_to_mviewer",
        "build_mviewer_tree_from_wms_capabilities",
    ),
    "convert_qgis_layers_to_mviewer_xml": (
        "qgisxmviewer.services.qgis_to_mviewer",
        "convert_qgis_layers_to_mviewer_xml",
    ),
    "create_mviewer_config_from_qgis_project": (
        "qgisxmviewer.services.qgis_to_mviewer",
        "create_mviewer_config_from_qgis_project",
    ),
    "create_mviewer_config_from_wms_capabilities": (
        "qgisxmviewer.services.qgis_to_mviewer",
        "create_mviewer_config_from_wms_capabilities",
    ),
    "create_mviewer_xml_text_from_qgis_project": (
        "qgisxmviewer.services.qgis_to_mviewer",
        "create_mviewer_xml_text_from_qgis_project",
    ),
    "create_mviewer_xml_text_from_wms_capabilities": (
        "qgisxmviewer.services.qgis_to_mviewer",
        "create_mviewer_xml_text_from_wms_capabilities",
    ),
    "read_qgis_server_project": (
        "qgisxmviewer.qgis_project",
        "read_qgis_server_project",
    ),
    "read_wms_capabilities": (
        "qgisxmviewer.wms_capabilities",
        "read_wms_capabilities",
    ),
}


def __getattr__(name: str) -> Any:
    """Lazily resolve public exports to avoid import cycles."""
    try:
        module_name, attribute_name = _EXPORTS[name]
    except KeyError as exc:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}") from exc
    module = import_module(module_name)
    return getattr(module, attribute_name)
