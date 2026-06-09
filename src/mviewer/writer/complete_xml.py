"""Complete mviewer XML configuration documents with theme and layer nodes."""

from copy import deepcopy
from xml.etree.ElementTree import Element, ElementTree, SubElement
import logging

from mviewer.exceptions import MviewerXmlError
from mviewer.utils import normalize_xml_id

LOGGER = logging.getLogger(__name__)


def complete_mviewer_xml(
    tree: ElementTree,
    layer_elements: list[Element],
    default_theme_name: str = "Projet QGIS",
) -> ElementTree:
    """Add layer elements to an existing mviewer XML configuration tree."""
    if not layer_elements:
        raise MviewerXmlError("Cannot complete a mviewer configuration without layers")

    root = tree.getroot()
    if root.tag != "config":
        raise MviewerXmlError(f"Unexpected mviewer XML root element: {root.tag}")

    themes = root.find("themes")
    if themes is None:
        themes = SubElement(root, "themes", {"mini": "false"})

    theme_by_id = _index_existing_themes(themes)
    group_by_theme_id: dict[str, dict[str, Element]] = {
        theme_id: _index_existing_groups(theme)
        for theme_id, theme in theme_by_id.items()
    }
    for layer in layer_elements:
        output_layer = deepcopy(layer)
        theme_name = output_layer.attrib.pop("theme", None) or default_theme_name
        group_name = output_layer.attrib.pop("group", None)
        theme_id = normalize_xml_id(theme_name)
        theme = theme_by_id.get(theme_id)
        if theme is None:
            theme = SubElement(
                themes,
                "theme",
                {
                    "id": theme_id,
                    "name": theme_name,
                    "collapsed": "false",
                    "icon": "fas fa-map",
                },
            )
            theme_by_id[theme_id] = theme
            group_by_theme_id[theme_id] = {}
            LOGGER.debug("Created mviewer theme %s", theme_id)
        if group_name:
            groups = group_by_theme_id[theme_id]
            group_id = normalize_xml_id(group_name)
            group = groups.get(group_id)
            if group is None:
                group = SubElement(
                    theme,
                    "group",
                    {
                        "id": group_id,
                        "name": group_name,
                    },
                )
                groups[group_id] = group
                LOGGER.debug("Created mviewer group %s in theme %s", group_id, theme_id)
            group.append(output_layer)
        else:
            theme.append(output_layer)

    return tree


def complete_xml(tree: ElementTree, layer_elements: list[Element]) -> ElementTree:
    """Complete an XML tree with mviewer layer elements."""
    return complete_mviewer_xml(tree, layer_elements)


def _index_existing_themes(themes: Element) -> dict[str, Element]:
    """Return existing mviewer themes keyed by normalized theme id."""
    indexed: dict[str, Element] = {}
    for theme in themes.findall("theme"):
        theme_id = theme.get("id") or normalize_xml_id(theme.get("name") or "qgis")
        indexed[theme_id] = theme
    return indexed


def _index_existing_groups(theme: Element) -> dict[str, Element]:
    """Return existing mviewer groups keyed by normalized group id."""
    indexed: dict[str, Element] = {}
    for group in theme.findall("group"):
        group_id = group.get("id") or normalize_xml_id(group.get("name") or "groupe")
        indexed[group_id] = group
    return indexed
