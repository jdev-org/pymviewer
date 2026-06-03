"""Build and write mviewer XML configuration documents."""

from io import BytesIO
from pathlib import Path
from xml.etree.ElementTree import Element, ElementTree, indent
import logging

from mviewer.exceptions import MviewerXmlError
from mviewer.writer.complete_xml import complete_mviewer_xml
from mviewer.writer.create_xml import create_mviewer_xml_skeleton

LOGGER = logging.getLogger(__name__)


def build_mviewer_xml(layer_elements: list[Element]) -> ElementTree:
    """Build a mviewer XML document from layer XML elements."""
    if not layer_elements:
        raise MviewerXmlError("Cannot build a mviewer configuration without layers")

    tree = create_mviewer_xml_skeleton()
    return complete_mviewer_xml(tree, layer_elements)


def write_mviewer_xml(tree: ElementTree, output_path: Path) -> Path:
    """Write a mviewer XML document to disk."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    indent(tree, space="    ")
    tree.write(path, encoding="UTF-8", xml_declaration=True)
    LOGGER.info("Wrote mviewer XML configuration to %s", path)
    return path


def serialize_mviewer_xml(tree: ElementTree) -> str:
    """Serialize a mviewer XML document to a UTF-8 string."""
    buffer = BytesIO()
    indent(tree, space="    ")
    tree.write(buffer, encoding="UTF-8", xml_declaration=True)
    return buffer.getvalue().decode("utf-8")
