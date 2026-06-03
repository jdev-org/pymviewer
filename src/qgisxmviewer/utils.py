"""Utility functions for QGIS project parsing."""

from pathlib import Path
from urllib.parse import parse_qsl, urlsplit
import re

from qgisxmviewer.exceptions import QgisProjectError


VALID_LAYER_TYPES = {"wms", "wfs", "geojson", "vector", "raster", "unknown"}


def validate_project_path(project_path: Path) -> Path:
    """Validate that a QGIS project path points to an existing readable file."""
    path = Path(project_path)
    if not path.exists():
        raise FileNotFoundError(f"QGIS project file does not exist: {path}")
    if not path.is_file():
        raise QgisProjectError(f"QGIS project path is not a file: {path}")
    if path.suffix.lower() not in {".qgs", ".xml"}:
        raise QgisProjectError(f"Unsupported QGIS project extension: {path.suffix}")
    return path


def validate_layer_type(layer_type: str) -> str:
    """Validate and return a supported internal layer type."""
    if layer_type not in VALID_LAYER_TYPES:
        raise QgisProjectError(f"Unsupported layer type: {layer_type}")
    return layer_type


def parse_qgis_datasource(source: str | None) -> dict[str, str]:
    """Extract useful key/value parameters from a QGIS datasource string."""
    if not source:
        return {}
    params: dict[str, str] = {}
    for key, value in re.findall(r"(\w+)='([^']*)'", source):
        params[key.lower()] = value
    for key, value in parse_qsl(source, keep_blank_values=True):
        params.setdefault(key.lower(), value)
    for token in source.split():
        if "=" in token and not token.startswith("|"):
            key, value = token.split("=", 1)
            params.setdefault(key.lower(), value.strip("'\""))
    if "?" in source:
        query = urlsplit(source).query
        for key, value in parse_qsl(query, keep_blank_values=True):
            params.setdefault(key.lower(), value)
    return params
