# TASKS.md

## Objectif

Créer une librairie Python installable via `pip` à partir du code existant de génération de configurations mviewer depuis QGIS Server.

Le code source actuel situé dans :

```txt
python/xml/qgis/*.py
python/qgis/*.py
```

doit être déplacé, transformé et vectorisé dans :

```txt
python/lib/qgisxmviewer
```

La librairie finale doit permettre :

- de lire un projet QGIS Server `.qgs` ;
- de lire un document WMS `GetCapabilities` ;
- de convertir les couches QGIS/WMS en modèles Python ;
- de générer une configuration XML mviewer valide ;
- d'être utilisée depuis un script, une API, un serveur MCP ou une CLI ;
- d'être publiée et installée avec `pip`.

---

## Contraintes

- Le code métier doit rester indépendant de FastAPI, MCP ou de mviewer côté navigateur.
- Les fonctions publiques doivent être typées et documentées avec des docstrings pydoc en anglais.
- Les dépendances de production doivent être open source.
- Ne pas ajouter de dépendance de production sans validation explicite.
- Préserver la compatibilité avec mviewer version 4+.
- Préserver les noms WMS réels dans les attributs `layers`.
- Générer des attributs `id` mviewer sûrs, normalisés et uniques.
- Encoder correctement les URL WMS et XML.
- Garder des modules courts, cohérents et testables.

---

## Structure cible

Structure recommandée :

```txt
python/lib/qgisxmviewer/
  pyproject.toml
  README.md
  LICENSE
  src/
    pymviewer/
      __init__.py
      exceptions.py
      models.py
      utils.py
      qgis_project.py
      wms_capabilities.py
      converters/
        __init__.py
        wms.py
        wfs.py
        geojson.py
      writer/
        __init__.py
        create_xml.py
        complete_xml.py
        mviewer_xml.py
      services/
        __init__.py
        qgis_to_mviewer.py
      cli.py
  tests/
    test_ids.py
    test_wms_capabilities.py
    test_wms_generation.py
    test_mviewer_xml.py
```

---

## Tâche 1 — Inventorier le code existant

Analyser et classer les fichiers existants :

```txt
python/xml/qgis/models.py
python/xml/qgis/exceptions.py
python/xml/qgis/utils.py
python/xml/qgis/readQgisServerProject.py
python/xml/qgis/readWmsCapabilities.py
python/xml/qgis/qgisWmsToXml.py
python/xml/qgis/qgisWfsToXml.py
python/xml/qgis/qgisGeojsonToXml.py
python/xml/qgis/createXml.py
python/xml/qgis/completeXml.py
python/xml/qgis/mviewerXmlWriter.py
python/xml/qgis/qgis.py
python/xml/qgis/callQgisProject.py
python/main.py
python/tests/
```

Livrable :

- tableau de correspondance ancien fichier -> nouveau module ;
- liste des fonctions publiques à conserver ;
- liste des fonctions internes à renommer ou déplacer.

---

## Tâche 2 — Créer le package Python

Créer un package `pymviewer` avec layout `src`.

À faire :

- ajouter `pyproject.toml` ;
- définir le nom du package : `pymviewer` ;
- définir une version initiale : `0.1.0` ;
- exposer les métadonnées minimales ;
- configurer `setuptools` ou `hatchling` sans dépendance inutile ;
- ajouter un entrypoint CLI :

```toml
[project.scripts]
pymviewer = "pymviewer.cli:main"
```

Critère d'acceptation :

```bash
python -m pip install -e python/lib/qgisxmviewer
pymviewer --help
```

---

## Tâche 3 — Déplacer les modèles et exceptions

Déplacer :

```txt
models.py -> src/pymviewer/qgisxmviewer/models.py
exceptions.py -> src/pymviewer/qgisxmviewer/exceptions.py
```

À vérifier :

- imports absolus depuis `pymviewer` ;
- dataclasses stables ;
- pas de dépendance au chemin du dépôt mviewer ;
- docstrings pydoc en anglais.

---

## Tâche 4 — Refactoriser les utilitaires

Déplacer et compléter :

```txt
utils.py -> src/pymviewer/qgisxmviewer/utils.py
```

Fonctions attendues :

- `normalize_xml_id(value: str) -> str`
- `unique_xml_id(value: str, used_ids: set[str]) -> str`
- `bool_to_xml(value: bool) -> str`
- `clean_service_url(service_base_url: str) -> str`
- `add_query_params(url: str, params: dict[str, str]) -> str`
- `normalize_wms_legend_url(legend_url: str | None) -> str | None`
- `rebase_url(url: str | None, base_url: str) -> str | None`
- `parse_qgis_datasource(source: str | None) -> dict[str, str]`

Tests minimum :

- id avec espaces ;
- id avec accents ;
- id vide ;
- doublons après normalisation ;
- URL WMS avec espaces ;
- `STYLE=défaut` vers `STYLE=default`.

---

## Tâche 5 — Refactoriser le lecteur QGIS Project

Déplacer :

```txt
readQgisServerProject.py -> src/pymviewer/qgisxmviewer/qgis_project.py
```

Fonction publique :

```python
def read_qgis_server_project(project_path: Path) -> list[QgisLayer]:
    """Read a QGIS Server project and return its published layers."""
```

À améliorer :

- gérer `.qgs` ;
- documenter explicitement que `.qgz` n'est pas encore supporté si non implémenté ;
- conserver l'ordre des couches ;
- conserver les groupes ;
- extraire CRS, extent, provider, datasource, shortname, title, abstract ;
- utiliser les exceptions de la librairie.

---

## Tâche 6 — Refactoriser le lecteur WMS GetCapabilities

Déplacer :

```txt
readWmsCapabilities.py -> src/pymviewer/qgisxmviewer/wms_capabilities.py
```

Fonction publique :

```python
def read_wms_capabilities(capabilities_path: Path) -> tuple[list[QgisLayer], str]:
    """Read a WMS GetCapabilities document and return layers plus service URL."""
```

À vérifier :

- namespaces WMS 1.3.0 ;
- URL de service ;
- couches nommées uniquement ;
- style et légende ;
- normalisation unique des ids ;
- conservation du nom WMS réel dans `published_name`.

---

## Tâche 7 — Refactoriser les convertisseurs

Déplacer :

```txt
qgisWmsToXml.py -> src/pymviewer/qgisxmviewer/converters/wms.py
qgisWfsToXml.py -> src/pymviewer/qgisxmviewer/converters/wfs.py
qgisGeojsonToXml.py -> src/pymviewer/qgisxmviewer/converters/geojson.py
```

Fonctions publiques :

```python
def qgis_wms_layer_to_mviewer_xml(layer: QgisLayer, service_base_url: str) -> Element:
    """Convert a QGIS WMS layer to a mviewer XML layer element."""

def qgis_wfs_layer_to_mviewer_xml(layer: QgisLayer, service_base_url: str) -> Element:
    """Convert a QGIS WFS layer to a mviewer XML layer element."""

def qgis_geojson_layer_to_mviewer_xml(layer: QgisLayer) -> Element:
    """Convert a QGIS GeoJSON layer to a mviewer XML layer element."""
```

Règles WMS :

- `id` = identifiant mviewer normalisé ;
- `name` = libellé utilisateur ;
- `layers` = nom WMS réel ;
- `url` = URL du service ;
- `legendurl` = URL encodée et basée sur le même service si override.

---

## Tâche 8 — Refactoriser le writer XML mviewer

Déplacer :

```txt
createXml.py -> src/pymviewer/qgisxmviewer/writer/create_xml.py
completeXml.py -> src/pymviewer/qgisxmviewer/writer/complete_xml.py
mviewerXmlWriter.py -> src/pymviewer/qgisxmviewer/writer/mviewer_xml.py
```

Fonctions publiques :

```python
def create_mviewer_xml_skeleton(...) -> ElementTree:
    """Create an empty mviewer XML configuration tree."""

def complete_mviewer_xml(...) -> ElementTree:
    """Add layer elements to an existing mviewer XML configuration tree."""

def build_mviewer_xml(layer_elements: list[Element]) -> ElementTree:
    """Build a mviewer XML document from layer XML elements."""

def write_mviewer_xml(tree: ElementTree, output_path: Path) -> Path:
    """Write a mviewer XML document to disk."""
```

À vérifier :

- structure compatible avec `apps/default.xml` ;
- un seul fond de plan visible ;
- groupes/thèmes générés correctement ;
- XML indenté et lisible.

---

## Tâche 9 — Créer les services publics

Créer :

```txt
src/pymviewer/qgisxmviewer/services/qgis_to_mviewer.py
```

Fonctions publiques :

```python
def create_mviewer_config_from_qgis_project(
    project_path: Path,
    output_path: Path,
    service_base_url: str,
) -> Path:
    """Create a mviewer XML configuration from a QGIS Server project."""

def create_mviewer_config_from_wms_capabilities(
    capabilities_path: Path,
    output_path: Path,
    service_base_url: str | None = None,
) -> Path:
    """Create a mviewer XML configuration from a WMS GetCapabilities file."""
```

Critères :

- aucune logique CLI dans ce module ;
- fonctions réutilisables depuis API, MCP, scripts et tests.

---

## Tâche 10 — Créer la CLI

Créer :

```txt
src/pymviewer/cli.py
```

Commandes recommandées :

```bash
pymviewer from-qgs \
  --project /path/to/project.qgs \
  --output /path/to/config.xml \
  --service-url http://localhost:90/ogc/data

pymviewer from-capabilities \
  --capabilities /path/to/GetCapabilities.xml \
  --output /path/to/config.xml \
  --service-url http://localhost:90/ogc/data
```

À faire :

- utiliser `argparse` ;
- configurer les logs ;
- retourner un code d'erreur non nul en cas d'échec ;
- ne pas contenir de logique métier.

---

## Tâche 11 — Adapter les imports existants

Une fois la librairie créée, décider si les anciens fichiers restent :

Option A — wrappers de compatibilité :

```txt
python/xml/qgis/*.py
```

réexportent les fonctions depuis `pymviewer`.

Option B — suppression après migration :

- supprimer les anciens fichiers ;
- adapter les appels existants ;
- documenter le changement.

Décision recommandée :

- garder temporairement des wrappers pour ne pas casser les usages existants.

---

## Tâche 12 — Tests

Créer une suite de tests dans :

```txt
python/lib/qgisxmviewer/tests
```

Tests minimum :

- normalisation d'id avec espaces ;
- normalisation d'id avec accents ;
- unicité des ids après normalisation ;
- parsing WMS GetCapabilities ;
- parsing QGIS `.qgs` minimal ;
- génération WMS avec `id`, `name`, `layers` distincts ;
- `legendurl` avec `STYLE=défaut` ;
- `legendurl` avec nom de couche contenant un espace ;
- override de `service_base_url` ;
- génération XML finale ;
- écriture du fichier XML.

La suite doit tourner avec :

```bash
python -m unittest discover -s python/lib/qgisxmviewer/tests
```

ou, si `pytest` est choisi plus tard :

```bash
pytest python/lib/qgisxmviewer/tests
```

---

## Tâche 13 — Documentation mkdoc material

Créer :

```txt
python/lib/qgisxmviewer/README.md
```

Contenu minimum :

- objectif de la librairie ;
- installation locale ;
- usage Python ;
- liste des paramètres type doc api
- usage CLI ;
- exemples depuis `.qgs` ;
- exemples depuis `GetCapabilities` ;
- limites connues ;
- compatibilité mviewer/QGIS Server.

---

## Tâche 14 — Packaging pip

Vérifier :

```bash
python -m pip install -e python/lib/qgisxmviewer
python -m build python/lib/qgisxmviewer
```

Ne pas ajouter `build` en dépendance de production.

Critères :

- installation editable fonctionnelle ;
- import Python fonctionnel :

```python
import pymviewer.qgisxmviewer
```

- CLI disponible :

```bash
pymviewer --help
```

---

## Tâche 15 — Nettoyage et compatibilité

À faire après migration :

- supprimer les chemins codés en dur ;
- éviter les imports relatifs fragiles ;
- documenter les anciens chemins ;
- vérifier que `python/xml/qgis/example/data.xml` peut encore être généré ;
- vérifier que `python/qgis/example/data.xml` n'est gardé que si mviewer l'utilise explicitement ;
- vérifier que les tests existants passent.

---

## Critères d'acceptation

Le chantier est terminé si :

- la librairie `pymviewer` est installable avec `pip install -e` ;
- les fonctions publiques sont importables depuis `pymviewer` ;
- la CLI permet de générer un XML depuis `.qgs` et `GetCapabilities` ;
- les ids mviewer sont sûrs et uniques ;
- les noms WMS réels sont conservés dans `layers` ;
- les `legendurl` sont correctement encodées ;
- les tests couvrent les cas critiques ;
- la documentation permet un premier usage autonome ;
- aucun nouveau package de production non validé n'a été ajouté.
