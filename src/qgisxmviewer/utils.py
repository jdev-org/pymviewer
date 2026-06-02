"""Utility functions for QGIS project parsing and mviewer XML output."""

from pathlib import Path
from urllib.parse import parse_qsl, quote, urlencode, urlsplit, urlunsplit
import re
import unicodedata

from qgisxmviewer.exceptions import QgisProjectError


VALID_LAYER_TYPES = {"wms", "wfs", "geojson", "vector", "raster", "unknown"}


def normalize_xml_id(value: str) -> str:
    """Normalize a string into a safe mviewer XML identifier.

    Args:
        value: Input text to normalize.

    Returns:
        Lowercase ASCII identifier using letters, numbers and underscores only.
    """
    normalized = unicodedata.normalize("NFKD", value or "layer")
    ascii_value = normalized.encode("ascii", "ignore").decode("ascii")
    xml_id = re.sub(r"[^A-Za-z0-9]+", "_", ascii_value).strip("_").lower()
    if not xml_id:
        return "layer"
    if not re.match(r"^[A-Za-z_]", xml_id):
        return f"layer_{xml_id}"
    return xml_id


def unique_xml_id(value: str, used_ids: set[str]) -> str:
    """Normalize a value into an id that is unique within ``used_ids``.

    Args:
        value: Input text to normalize.
        used_ids: Mutable set of identifiers already allocated.

    Returns:
        A normalized id. If needed, ``_2``, ``_3`` and following suffixes are
        appended until the identifier is unique.
    """
    base_id = normalize_xml_id(value)
    candidate = base_id
    suffix = 2
    while candidate in used_ids:
        candidate = f"{base_id}_{suffix}"
        suffix += 1
    used_ids.add(candidate)
    return candidate


def bool_to_xml(value: bool) -> str:
    """Convert a Python boolean to a lowercase XML boolean string."""
    return "true" if value else "false"


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


def clean_service_url(service_base_url: str) -> str:
    """Normalize a service URL while preserving existing query parameters."""
    if not service_base_url:
        raise ValueError("Service base URL is required")
    return service_base_url.strip()


def add_query_params(url: str, params: dict[str, str]) -> str:
    """Return a URL with query parameters merged into existing parameters."""
    parts = urlsplit(clean_service_url(url))
    query = dict(parse_qsl(parts.query, keep_blank_values=True))
    query.update(params)
    return urlunsplit(
        (parts.scheme, parts.netloc, parts.path, urlencode(query, quote_via=quote), parts.fragment)
    )


def normalize_wms_legend_url(legend_url: str | None) -> str | None:
    """Normalize and encode a WMS legend URL for XML serialization.

    Args:
        legend_url: Raw legend URL read from capabilities.

    Returns:
        A URL with encoded query parameter values and normalized style value,
        or ``None`` when no URL was provided.
    """
    if not legend_url:
        return None
    parts = urlsplit(legend_url)
    query = []
    for key, value in parse_qsl(parts.query, keep_blank_values=True):
        if key.lower() == "style" and value.lower() in {"défaut", "defaut"}:
            value = "default"
        query.append((key, value))
    return urlunsplit(
        (parts.scheme, parts.netloc, parts.path, urlencode(query, quote_via=quote), parts.fragment)
    )


def encode_wms_layer_name(layer_name: str | None) -> str | None:
    """Encode a WMS layer name the same way it appears in query parameters."""
    if not layer_name:
        return None
    return quote(layer_name, safe="")


def rebase_url(url: str | None, base_url: str) -> str | None:
    """Replace an URL scheme, host and path with a service base URL.

    Query parameters and fragments from ``url`` are preserved.
    """
    if not url:
        return None
    original = urlsplit(url)
    base = urlsplit(clean_service_url(base_url))
    return urlunsplit((base.scheme, base.netloc, base.path, original.query, original.fragment))


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
