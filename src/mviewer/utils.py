"""Utility helpers for mviewer XML generation and OGC URL normalization."""

from urllib.parse import parse_qsl, quote, urlencode, urlsplit, urlunsplit
import re
import unicodedata


def normalize_xml_id(value: str) -> str:
    """Normalize a string into a safe mviewer XML identifier."""
    normalized = unicodedata.normalize("NFKD", value or "layer")
    ascii_value = normalized.encode("ascii", "ignore").decode("ascii")
    xml_id = re.sub(r"[^A-Za-z0-9]+", "_", ascii_value).strip("_").lower()
    if not xml_id:
        return "layer"
    if not re.match(r"^[A-Za-z_]", xml_id):
        return f"layer_{xml_id}"
    return xml_id


def unique_xml_id(value: str, used_ids: set[str]) -> str:
    """Normalize a value into an id unique within ``used_ids``."""
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
        (
            parts.scheme,
            parts.netloc,
            parts.path,
            urlencode(query, quote_via=quote),
            parts.fragment,
        )
    )


def normalize_wms_legend_url(legend_url: str | None) -> str | None:
    """Normalize and encode a WMS legend URL for XML serialization."""
    if not legend_url:
        return None
    parts = urlsplit(legend_url)
    query = []
    for key, value in parse_qsl(parts.query, keep_blank_values=True):
        if key.lower() == "style" and value.lower() in {"défaut", "defaut"}:
            value = "default"
        query.append((key, value))
    return urlunsplit(
        (
            parts.scheme,
            parts.netloc,
            parts.path,
            urlencode(query, quote_via=quote),
            parts.fragment,
        )
    )


def encode_wms_layer_name(layer_name: str | None) -> str | None:
    """Encode a WMS layer name exactly as published by the OGC service."""
    if not layer_name:
        return None
    return quote(layer_name.strip(), safe="")


def rebase_url(url: str | None, base_url: str) -> str | None:
    """Replace a URL scheme, host and path with a service base URL."""
    if not url:
        return None
    original = urlsplit(url)
    base = urlsplit(clean_service_url(base_url))
    return urlunsplit(
        (base.scheme, base.netloc, base.path, original.query, original.fragment)
    )
