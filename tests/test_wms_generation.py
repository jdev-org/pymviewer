"""Tests for WMS capabilities to mviewer XML generation."""

from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from qgisxmviewer.models import QgisLayer
from qgisxmviewer.services.qgis_to_mviewer import convert_qgis_layers_to_mviewer_xml
from qgisxmviewer.wms_capabilities import read_wms_capabilities
from qgisxmviewer.utils import (
    encode_wms_layer_name,
    normalize_xml_id,
    normalize_wms_legend_url,
    unique_xml_id,
)


class WmsGenerationTest(unittest.TestCase):
    """Validate mviewer WMS XML generation edge cases."""

    def test_normalize_id_with_spaces(self) -> None:
        """Layer ids with spaces should use underscores."""
        self.assertEqual(normalize_xml_id("Contributeurs QGIS"), "contributeurs_qgis")

    def test_normalize_id_with_accents(self) -> None:
        """Layer ids with accents should be converted to ASCII."""
        self.assertEqual(
            normalize_xml_id("Réserves naturelles régionales"),
            "reserves_naturelles_regionales",
        )

    def test_unique_id_suffix_for_duplicates(self) -> None:
        """Duplicate normalized ids should receive a numeric suffix."""
        used_ids: set[str] = set()
        first = unique_xml_id("Réserves naturelles régionales", used_ids)
        second = unique_xml_id("Reserves naturelles regionales", used_ids)
        self.assertEqual(first, "reserves_naturelles_regionales")
        self.assertEqual(second, "reserves_naturelles_regionales_2")

    def test_legend_url_style_default_and_layer_encoding(self) -> None:
        """Legend URLs should normalize style and encode layer names."""
        url = (
            "http://localhost/ogc/data?SERVICE=WMS&REQUEST=GetLegendGraphic"
            "&LAYER=Contributeurs QGIS&STYLE=défaut"
        )
        self.assertEqual(
            normalize_wms_legend_url(url),
            "http://localhost/ogc/data?SERVICE=WMS&REQUEST=GetLegendGraphic"
            "&LAYER=Contributeurs%20QGIS&STYLE=default",
        )

    def test_encode_wms_layer_name_with_apostrophe(self) -> None:
        """WMS layer names should be encoded like URL query parameter values."""
        self.assertEqual(encode_wms_layer_name("Cours d'eau"), "Cours%20d%27eau")

    def test_capabilities_generation_keeps_wms_name_in_layers(self) -> None:
        """Generated XML should separate mviewer id from WMS layer name."""
        with TemporaryDirectory() as directory:
            capabilities_path = Path(directory) / "capabilities.xml"
            capabilities_path.write_text(_capabilities_xml(), encoding="utf-8")
            layers, service_url = read_wms_capabilities(capabilities_path)
            xml_layers = convert_qgis_layers_to_mviewer_xml(layers, service_url)

        first, second = xml_layers
        self.assertEqual(first.get("id"), "contributeurs_qgis")
        self.assertEqual(first.get("name"), "Contributeurs QGIS")
        self.assertEqual(first.get("layers"), "Contributeurs%20QGIS")
        self.assertIn("LAYER=Contributeurs%20QGIS", first.get("legendurl") or "")
        self.assertIn("STYLE=default", first.get("legendurl") or "")
        self.assertEqual(second.get("id"), "contributeurs_qgis_2")

    def test_capabilities_generation_encodes_apostrophe_in_layers(self) -> None:
        """Generated XML should encode apostrophes in WMS layer names."""
        with TemporaryDirectory() as directory:
            capabilities_path = Path(directory) / "capabilities.xml"
            capabilities_path.write_text(_capabilities_xml_with_apostrophe(), encoding="utf-8")
            layers, service_url = read_wms_capabilities(capabilities_path)
            [xml_layer] = convert_qgis_layers_to_mviewer_xml(layers, service_url)

        self.assertEqual(xml_layer.get("name"), "Cours d'eau")
        self.assertEqual(xml_layer.get("layers"), "Cours%20d%27eau")

    def test_service_override_rebases_legend_url(self) -> None:
        """Legend URLs should use the same base URL as generated WMS layers."""
        with TemporaryDirectory() as directory:
            capabilities_path = Path(directory) / "capabilities.xml"
            capabilities_path.write_text(_capabilities_xml(), encoding="utf-8")
            layers, _service_url = read_wms_capabilities(capabilities_path)
            xml_layers = convert_qgis_layers_to_mviewer_xml(
                layers,
                "http://localhost:90/ogc/data",
            )

        self.assertEqual(xml_layers[0].get("url"), "http://localhost:90/ogc/data")
        self.assertTrue(
            (xml_layers[0].get("legendurl") or "").startswith(
                "http://localhost:90/ogc/data?"
            )
        )

    def test_wms_xyz_layer_sets_xyz_attribute_and_tile_url(self) -> None:
        """XYZ layers declared through the WMS provider should be exported as XYZ."""
        layer = QgisLayer(
            id="openstreetmap",
            name="OpenStreetMap",
            title="OpenStreetMap",
            provider="wms",
            source=(
                "crs=EPSG:3857&format&type=xyz&"
                "url=https://tile.openstreetmap.org/%7Bz%7D/%7Bx%7D/%7By%7D.png&zmax=19&zmin=0"
            ),
            layer_type="wms",
            group="Basemaps",
            visible=True,
            crs="EPSG:3857",
            xyz=True,
        )

        [xml_layer] = convert_qgis_layers_to_mviewer_xml([layer], "http://localhost:90/ogc/data")

        self.assertEqual(xml_layer.get("type"), "wms")
        self.assertEqual(xml_layer.get("xyz"), "true")
        self.assertEqual(
            xml_layer.get("url"),
            "https://tile.openstreetmap.org/{z}/{x}/{y}.png",
        )
        self.assertIsNone(xml_layer.get("layers"))


def _capabilities_xml() -> str:
    """Return a minimal WMS capabilities document for tests."""
    return """<?xml version="1.0" encoding="utf-8"?>
<WMS_Capabilities version="1.3.0"
    xmlns="http://www.opengis.net/wms"
    xmlns:xlink="http://www.w3.org/1999/xlink">
  <Service>
    <Title>data</Title>
    <OnlineResource xlink:href="http://localhost/ogc/data"/>
  </Service>
  <Capability>
    <Layer>
      <Title>data</Title>
      <Layer queryable="1">
        <Name>Contributeurs QGIS</Name>
        <Title>Contributeurs QGIS</Title>
        <Style>
          <Name>défaut</Name>
          <LegendURL>
            <OnlineResource xlink:href="http://localhost/ogc/data?SERVICE=WMS&amp;REQUEST=GetLegendGraphic&amp;LAYER=Contributeurs QGIS&amp;STYLE=défaut"/>
          </LegendURL>
        </Style>
      </Layer>
      <Layer queryable="1">
        <Name>Contributeurs-QGIS</Name>
        <Title>Contributeurs QGIS duplicate</Title>
      </Layer>
    </Layer>
  </Capability>
</WMS_Capabilities>
"""


def _capabilities_xml_with_apostrophe() -> str:
    """Return a minimal WMS capabilities document with an apostrophe in the name."""
    return """<?xml version="1.0" encoding="utf-8"?>
<WMS_Capabilities version="1.3.0"
    xmlns="http://www.opengis.net/wms"
    xmlns:xlink="http://www.w3.org/1999/xlink">
  <Service>
    <Title>data</Title>
    <OnlineResource xlink:href="http://localhost/ogc/data"/>
  </Service>
  <Capability>
    <Layer>
      <Title>data</Title>
      <Layer queryable="1">
        <Name>Cours d'eau</Name>
        <Title>Cours d'eau</Title>
      </Layer>
    </Layer>
  </Capability>
</WMS_Capabilities>
"""


if __name__ == "__main__":
    unittest.main()
