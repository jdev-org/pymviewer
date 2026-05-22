"""Build and write mviewer XML configuration documents."""

from pathlib import Path
from xml.etree.ElementTree import Element, ElementTree, indent
import logging

from qgisxmviewer.exceptions import MviewerXmlError
from qgisxmviewer.writer.complete_xml import complete_mviewer_xml
from qgisxmviewer.writer.create_xml import create_mviewer_xml_skeleton

LOGGER = logging.getLogger(__name__)


def build_mviewer_xml(layer_elements: list[Element]) -> ElementTree:
    """Build a mviewer XML document from layer XML elements.

    Args:
        layer_elements: Layer elements already converted to mviewer format.

    Returns:
        XML tree ready to write to disk.

    Raises:
        MviewerXmlError: If no layer element is provided.
    """
    if not layer_elements:
        raise MviewerXmlError("Cannot build a mviewer configuration without layers")

    tree = create_mviewer_xml_skeleton()
    return complete_mviewer_xml(tree, layer_elements)


def write_mviewer_xml(tree: ElementTree, output_path: Path) -> Path:
    """Write a mviewer XML document to disk.

    Args:
        tree: XML tree to write.
        output_path: Destination file path.

    Returns:
        The destination path.
    """
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    indent(tree, space="    ")
    tree.write(path, encoding="UTF-8", xml_declaration=True)
    LOGGER.info("Wrote mviewer XML configuration to %s", path)
    return path
