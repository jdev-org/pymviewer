"""Create base mviewer XML configuration documents."""

from xml.etree.ElementTree import Element, ElementTree, SubElement


DEFAULT_APPLICATION_ATTRIBUTES = {
    "title": "Projet QGIS",
    "logo": "",
    "help": "",
    "measuretools": "true",
    "exportpng": "true",
}

DEFAULT_MAPOPTIONS_ATTRIBUTES = {
    "projection": "EPSG:3857",
    "center": "0,0",
    "zoom": "2",
}

DEFAULT_BASELAYER_ATTRIBUTES = {
    "visible": "true",
    "type": "OSM",
    "id": "openstreetmap",
    "label": "OpenStreetMap",
    "title": "OpenStreetMap",
    "url": "https://{a-c}.tile.openstreetmap.org/{z}/{x}/{y}.png",
    "thumbgallery": "img/basemap/osm.png",
}


def create_mviewer_xml_skeleton(
    application_attributes: dict[str, str] | None = None,
    mapoptions_attributes: dict[str, str] | None = None,
    include_default_baselayer: bool = True,
) -> ElementTree:
    """Create an empty mviewer XML configuration tree.

    Args:
        application_attributes: Attributes merged into the ``application`` node.
        mapoptions_attributes: Attributes merged into the ``mapoptions`` node.
        include_default_baselayer: Whether to add an OpenStreetMap base layer.

    Returns:
        An XML tree containing the common mviewer configuration sections.
    """
    root = Element("config")
    SubElement(
        root,
        "application",
        _merge_attributes(DEFAULT_APPLICATION_ATTRIBUTES, application_attributes),
    )
    SubElement(
        root,
        "mapoptions",
        _merge_attributes(DEFAULT_MAPOPTIONS_ATTRIBUTES, mapoptions_attributes),
    )

    baselayers = SubElement(root, "baselayers", {"style": "gallery"})
    if include_default_baselayer:
        SubElement(baselayers, "baselayer", DEFAULT_BASELAYER_ATTRIBUTES.copy())

    SubElement(root, "themes", {"mini": "false"})
    return ElementTree(root)


def create_empty_xml() -> ElementTree:
    """Create a default empty mviewer XML configuration tree."""
    return create_mviewer_xml_skeleton()


def _merge_attributes(
    defaults: dict[str, str], overrides: dict[str, str] | None
) -> dict[str, str]:
    """Merge XML attributes while ignoring ``None`` override values."""
    attributes = defaults.copy()
    if overrides:
        attributes.update(
            {key: value for key, value in overrides.items() if value is not None}
        )
    return attributes
