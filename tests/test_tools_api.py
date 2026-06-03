"""Tests for the tool-friendly pymviewer API."""

from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from tools.python import (
    create_wfs_layer_structure_tool,
    create_wms_layer_structure_tool,
    generate_mviewer_from_capabilities_tool,
    generate_mviewer_from_qgs_tool,
    inspect_qgs_layers_tool,
    inspect_wms_capabilities_tool,
)


class ToolsApiTest(unittest.TestCase):
    """Validate serializable wrappers intended for MCP tools."""

    def test_create_wms_layer_structure_returns_mviewer_attributes(self) -> None:
        """WMS tool should return a serializable layer element structure."""
        result = create_wms_layer_structure_tool(
            service_url="http://localhost:90/ogc/data",
            layer_id="cadastre",
            name="Cadastre",
            published_name="cadastre_layer",
            group="Reference",
            visible=True,
            queryable=False,
            legend_url=(
                "http://localhost/ogc/data?SERVICE=WMS&REQUEST=GetLegendGraphic"
                "&LAYER=cadastre_layer"
            ),
        )

        self.assertEqual(result["tag"], "layer")
        self.assertEqual(result["attributes"]["type"], "wms")
        self.assertEqual(result["attributes"]["id"], "cadastre")
        self.assertEqual(result["attributes"]["layers"], "cadastre_layer")
        self.assertEqual(result["attributes"]["visible"], "true")
        self.assertEqual(result["attributes"]["queryable"], "false")

    def test_create_wms_layer_structure_accepts_layer_info_json(self) -> None:
        """WMS tool should accept a plain JSON-compatible layer structure."""
        result = create_wms_layer_structure_tool(
            service_url="http://localhost:90/ogc/data",
            layer_info={
                "id": "cadastre",
                "name": "Cadastre",
                "published_name": "cadastre_layer",
                "group": "Reference",
                "visible": True,
            },
        )

        self.assertEqual(result["attributes"]["id"], "cadastre")
        self.assertEqual(result["attributes"]["layers"], "cadastre_layer")
        self.assertEqual(result["attributes"]["visible"], "true")

    def test_create_wms_layer_structure_accepts_serialized_qgis_layer(self) -> None:
        """WMS tool should accept a serialized QGIS layer mapping."""
        result = create_wms_layer_structure_tool(
            service_url="http://localhost:90/ogc/data",
            qgis_layer={
                "id": "cadastre",
                "name": "Cadastre",
                "title": "Cadastre",
                "provider": "wms",
                "source": None,
                "layer_type": "wms",
                "group": "Reference",
                "visible": False,
                "crs": "EPSG:3857",
                "abstract": None,
                "extent": None,
                "published_name": "cadastre_layer",
                "short_name": None,
                "queryable": True,
                "wms_published": True,
                "wfs_published": False,
                "xyz": False,
                "legend_url": None,
                "metadata": {},
            },
        )

        self.assertEqual(result["attributes"]["id"], "cadastre")
        self.assertEqual(result["attributes"]["layers"], "cadastre_layer")
        self.assertEqual(result["attributes"]["queryable"], "true")

    def test_create_wfs_layer_structure_returns_mviewer_attributes(self) -> None:
        """WFS tool should return a serializable layer element structure."""
        result = create_wfs_layer_structure_tool(
            layer_id="parcels",
            name="Parcels",
            published_name="demo:parcels",
            service_url="http://localhost:90/ogc/data",
            group="Reference",
        )

        self.assertEqual(result["tag"], "layer")
        self.assertEqual(result["attributes"]["type"], "geojson")
        self.assertEqual(result["attributes"]["id"], "parcels")
        self.assertIn("SERVICE=WFS", result["attributes"]["url"])
        self.assertIn("TYPENAME=demo%3Aparcels", result["attributes"]["url"])

    def test_generate_from_capabilities_inline_returns_xml(self) -> None:
        """Inline generation should return XML content instead of a file path."""
        with TemporaryDirectory() as directory:
            capabilities_path = Path(directory) / "capabilities.xml"
            capabilities_path.write_text(_capabilities_xml(), encoding="utf-8")

            result = generate_mviewer_from_capabilities_tool(str(capabilities_path))

        self.assertEqual(result["mode"], "inline")
        self.assertIn("<?xml", result["xml"])
        self.assertIn("Contributeurs QGIS", result["xml"])
        self.assertEqual(result["capabilities_path"], str(capabilities_path))

    def test_generate_from_capabilities_file_returns_output_path(self) -> None:
        """File generation should write XML and return the output path."""
        with TemporaryDirectory() as directory:
            capabilities_path = Path(directory) / "capabilities.xml"
            output_path = Path(directory) / "generated.xml"
            capabilities_path.write_text(_capabilities_xml(), encoding="utf-8")

            result = generate_mviewer_from_capabilities_tool(
                str(capabilities_path),
                output_path=str(output_path),
            )

            self.assertEqual(result["mode"], "file")
            self.assertEqual(result["output_path"], str(output_path))
            self.assertTrue(output_path.exists())

    def test_generate_from_qgs_inline_returns_xml(self) -> None:
        """QGIS project generation should be usable without writing to disk."""
        with TemporaryDirectory() as directory:
            project_path = Path(directory) / "project.qgs"
            project_path.write_text(
                _qgis_project_xml_with_wms_datasource_layer(),
                encoding="utf-8",
            )

            result = generate_mviewer_from_qgs_tool(
                str(project_path),
                "http://localhost:90/ogc/pomme",
            )

        self.assertEqual(result["mode"], "inline")
        self.assertIn("<?xml", result["xml"])
        self.assertIn("environnement_hydrologie", result["xml"])
        self.assertEqual(result["service_url"], "http://localhost:90/ogc/pomme")

    def test_inspect_qgs_layers_returns_serializable_layers(self) -> None:
        """Project inspection should expose plain dictionaries."""
        with TemporaryDirectory() as directory:
            project_path = Path(directory) / "project.qgs"
            project_path.write_text(
                _qgis_project_xml_with_wms_datasource_layer(),
                encoding="utf-8",
            )

            result = inspect_qgs_layers_tool(str(project_path))

        self.assertEqual(result["layer_count"], 1)
        self.assertEqual(
            result["layers"][0]["published_name"], "environnement_hydrologie"
        )
        self.assertEqual(result["layers"][0]["extent"], None)

    def test_inspect_capabilities_returns_service_url(self) -> None:
        """Capabilities inspection should expose the detected service URL."""
        with TemporaryDirectory() as directory:
            capabilities_path = Path(directory) / "capabilities.xml"
            capabilities_path.write_text(_capabilities_xml(), encoding="utf-8")

            result = inspect_wms_capabilities_tool(str(capabilities_path))

        self.assertEqual(result["layer_count"], 2)
        self.assertEqual(result["service_url"], "http://localhost/ogc/data")
        self.assertEqual(result["layers"][0]["id"], "Contributeurs QGIS")

    def test_generate_from_qgs_rejects_blank_required_arguments(self) -> None:
        """Tool wrappers should fail fast on blank user input."""
        with self.assertRaises(ValueError):
            generate_mviewer_from_qgs_tool("   ", "http://localhost")


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
      </Layer>
      <Layer queryable="1">
        <Name>Contributeurs-QGIS</Name>
        <Title>Contributeurs QGIS duplicate</Title>
      </Layer>
    </Layer>
  </Capability>
</WMS_Capabilities>
"""


def _qgis_project_xml_with_wms_datasource_layer() -> str:
    """Return a minimal QGIS project with a WMS datasource ``layers`` value."""
    return """<?xml version="1.0" encoding="UTF-8"?>
<qgis>
  <layer-tree-group>
    <layer-tree-layer
        id="layer-1"
        name="Cours d'eau"
        checked="Qt::Checked"
        providerKey="wms"
        source="crs=EPSG:3857&amp;dpiMode=7&amp;featureCount=10&amp;format=image/png&amp;layers=environnement_hydrologie&amp;styles&amp;url=http://localhost:90/ogc/pomme"/>
  </layer-tree-group>
  <projectlayers>
    <maplayer type="vector">
      <id>layer-1</id>
      <layername>Cours d'eau</layername>
      <shortname>cours_d_eau</shortname>
      <provider>wms</provider>
      <datasource>contextualWMSLegend=0&amp;crs=EPSG:3857&amp;dpiMode=7&amp;featureCount=10&amp;format=image/png&amp;layers=environnement_hydrologie&amp;styles&amp;url=http://localhost:90/ogc/pomme</datasource>
      <title>Cours d'eau</title>
      <srs>
        <spatialrefsys>
          <authid>EPSG:3857</authid>
        </spatialrefsys>
      </srs>
    </maplayer>
  </projectlayers>
</qgis>
"""
