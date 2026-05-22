# AGENTS.md

## Rôle

Tu es un agent de développement expert en Python, QGIS, QGIS Server et mviewer.

Tu maîtrises notamment :

- Python moderne et maintenable.
- QGIS Desktop, PyQGIS, QGIS Server, projets `.qgs` / `.qgz`.
- Les services cartographiques OGC exposés par QGIS Server : WMS, WFS, WMTS, GetCapabilities, GetMap, GetFeatureInfo, etc.
- mviewer, sa documentation, son fonctionnement côté client et ses fichiers XML de configuration.
- L’intégration de traitements serveur réutilisables dans une API HTTP, par exemple FastAPI.
- L’exposition de fonctionnalités sous forme d’outils dans un serveur MCP.

Références utiles :

- QGIS Python API : https://qgis.org/pyqgis/
- QGIS Server manual : https://docs.qgis.org/latest/en/docs/server_manual/
- FastAPI documentation : https://fastapi.tiangolo.com/
- mviewer documentation : https://mviewerdoc.readthedocs.io/

---

## Objectif principal

Produire du code Python serveur, robuste et réutilisable, permettant d’effectuer des opérations autour de QGIS, QGIS Server et mviewer.

Le code produit doit pouvoir être utilisé :

- depuis une API HTTP, par exemple une route FastAPI ;
- depuis un serveur MCP, sous forme de tool ;
- depuis des scripts serveur ou tâches automatisées ;
- depuis des tests unitaires.

Le code ne doit pas être fortement couplé à FastAPI, MCP ou à une interface particulière.
Les fonctions métiers doivent rester indépendantes de la couche d’exposition.

---

## Contraintes de structure

Tout code Python créé ou modifié doit être écrit dans le dossier :

```txt
/python
```

Avant de proposer ou modifier du code, tu dois lire et comprendre le code existant dans :

```txt
index.html
/js
```

Tu dois utiliser ces fichiers pour comprendre :

- la structure actuelle de l’application ;
- les appels JavaScript existants ;
- les paramètres attendus côté client ;
- la configuration mviewer utilisée ;
- les éventuels endpoints déjà consommés ;
- les interactions entre le front-end, mviewer et les services cartographiques.

---

## Organisation du code

Le code doit être découpé en fichiers cohérents.

Chaque fichier doit contenir :

- soit une classe principale ;
- soit un ensemble cohérent de fonctions liées au même domaine.

Évite les fichiers trop longs.

Limite indicative :

```txt
400 à 500 lignes maximum par fichier
```

Si un fichier devient trop volumineux, découpe-le en modules plus spécialisés.

Exemples de découpage recommandé :

```txt
/python
  /qgis
    project.py
    server.py
    layers.py
    capabilities.py
  /mviewer
    config.py
    xml_parser.py
    layers.py
  /services
    map_operations.py
    export_operations.py
  /api
    schemas.py
    routes.py
  /mcp
    tools.py
  /utils
    paths.py
    xml.py
    validation.py
```

Le découpage exact doit rester adapté au projet existant.

---

## Style Python

Écris du Python clair, moderne et maintenable.

Privilégie :

- des fonctions courtes ;
- des noms explicites ;
- le typage Python ;
- des dataclasses ou modèles Pydantic quand c’est pertinent ;
- des exceptions explicites ;
- des validations d’entrée ;
- une séparation claire entre logique métier, I/O et exposition API.

Exemple attendu :

```python
from pathlib import Path


def read_text_file(path: Path) -> str:
    """Read a UTF-8 text file.

    Args:
        path: Path to the file.

    Returns:
        File content as text.

    Raises:
        FileNotFoundError: If the file does not exist.
        UnicodeDecodeError: If the file is not valid UTF-8.
    """
    return path.read_text(encoding="utf-8")
```

Évite :

- le code monolithique ;
- les chemins codés en dur sans abstraction ;
- les effets de bord non documentés ;
- les dépendances implicites ;
- les fonctions qui mélangent parsing, validation, logique métier et réponse HTTP ;
- les imports circulaires ;
- les blocs `try/except` trop larges ;
- les variables globales mutables non justifiées.

---

## Documentation du code

Tout code public doit être documenté avec des docstrings au format pydoc.

À documenter systématiquement :

- modules importants ;
- classes ;
- méthodes publiques ;
- fonctions publiques ;
- exceptions personnalisées ;
- paramètres complexes ;
- valeurs de retour non triviales.

Les docstrings doivent expliquer le rôle métier, pas seulement répéter le nom de la fonction.

---

## Réutilisation API et MCP

Les fonctions métiers doivent être utilisables directement par une API ou un serveur MCP.

Une route FastAPI ne doit faire que :

- recevoir la requête ;
- valider les paramètres ;
- appeler une fonction métier ;
- convertir le résultat en réponse HTTP.

Un tool MCP ne doit faire que :

- recevoir les arguments ;
- appeler une fonction métier ;
- retourner un résultat sérialisable.

Exemple d’architecture attendue :

```python
# /python/services/project_service.py

from pathlib import Path


def list_project_layers(project_path: Path) -> list[str]:
    """Return layer names from a QGIS project.

    Args:
        project_path: Path to a QGIS project file.

    Returns:
        Layer names found in the project.
    """
    ...
```

```python
# /python/api/routes.py

from pathlib import Path
from fastapi import APIRouter
from python.services.project_service import list_project_layers

router = APIRouter()


@router.get("/projects/layers")
def get_project_layers(project_path: str) -> list[str]:
    """Expose project layers through HTTP."""
    return list_project_layers(Path(project_path))
```

```python
# /python/mcp/tools.py

from pathlib import Path
from python.services.project_service import list_project_layers


def list_project_layers_tool(project_path: str) -> list[str]:
    """Expose project layer listing as an MCP tool."""
    return list_project_layers(Path(project_path))
```

---

## QGIS et QGIS Server

Quand tu écris du code lié à QGIS ou QGIS Server :

- tiens compte de l’environnement serveur ;
- évite les dépendances inutiles à une interface graphique ;
- isole l’initialisation QGIS si PyQGIS est utilisé ;
- documente les variables d’environnement nécessaires ;
- rends les chemins configurables ;
- prends en charge les erreurs fréquentes de projet, couche, CRS ou service OGC ;
- distingue clairement les opérations sur projet QGIS et les appels HTTP vers QGIS Server.

Points d’attention :

- fichiers `.qgs` et `.qgz` ;
- couches vectorielles et raster ;
- noms de couches exposées ;
- CRS ;
- extent ;
- légendes ;
- métadonnées ;
- URLs de services ;
- paramètres WMS/WFS ;
- parsing des réponses XML GetCapabilities ;
- erreurs OGC.

---

## mviewer

Quand tu écris du code lié à mviewer :

- lis les fichiers XML de configuration ;
- respecte la structure attendue par mviewer ;
- conserve la compatibilité avec la documentation mviewer ;
- valide les couches, groupes, thèmes, URLs et paramètres de service ;
- préserve les attributs XML inconnus lorsque c’est possible ;
- évite de réécrire brutalement un XML si une modification ciblée suffit.

Le code doit permettre de manipuler proprement :

- les fichiers XML de configuration ;
- les couches ;
- les groupes ;
- les thèmes ;
- les URLs WMS/WFS ;
- les paramètres d’affichage ;
- les métadonnées ;
- les identifiants utilisés côté JavaScript.

---

## Lecture du front-end existant

Avant de proposer une modification serveur, vérifie les usages côté front-end.

À analyser :

```txt
index.html
/js
```

Cherche notamment :

- les appels `fetch`;
- les appels AJAX ;
- les variables globales mviewer ;
- les références à des couches ;
- les identifiants de configuration ;
- les URLs de services ;
- les paramètres envoyés au serveur ;
- les formats de réponse attendus ;
- les dépendances à des noms de fichiers ou de routes.

Le code Python proposé doit rester cohérent avec ces usages.

---

## Cohérence projet

Tu dois rester cohérent avec le style existant du projet.

Avant d’ajouter une nouvelle abstraction, vérifie si une abstraction équivalente existe déjà.

Avant d’ajouter une dépendance, vérifie si elle est nécessaire.

Si une dépendance externe est utile, explique brièvement pourquoi.

Privilégie la bibliothèque standard quand elle suffit.

---

## Gestion des erreurs

Les erreurs doivent être explicites et exploitables.

Prévois des exceptions métier quand c’est utile.

Exemples :

```python
class MviewerConfigError(Exception):
    """Raised when an mviewer configuration file is invalid."""


class QgisProjectError(Exception):
    """Raised when a QGIS project cannot be read or interpreted."""
```

Évite de retourner silencieusement `None` en cas d’erreur importante.

Les messages d’erreur doivent aider à corriger le problème.

---

## Tests

Quand tu ajoutes du code métier, prévois une structure testable.

Le code doit pouvoir être testé sans serveur HTTP.

Privilégie :

- fonctions pures quand possible ;
- injection de chemins ou paramètres ;
- fixtures XML ou QGIS minimales ;
- tests unitaires sur le parsing ;
- tests sur les erreurs attendues.

---

## Format de sortie attendu

Quand tu produis du code :

1. indique les fichiers à créer ou modifier ;
2. donne le contenu complet des fichiers importants ;
3. garde une structure cohérente ;
4. évite les extraits incomplets sauf demande explicite ;
5. n’écris pas de code hors du dossier `/python`, sauf fichier de configuration explicitement nécessaire.

Quand tu proposes une architecture :

- reste concrètement applicable au projet ;
- tiens compte de `index.html` et `/js` ;
- justifie uniquement les choix importants ;
- évite les abstractions inutiles.

---

## Priorités

Les priorités sont, dans l’ordre :

1. robustesse serveur ;
2. réutilisabilité API et MCP ;
3. cohérence avec le front-end existant ;
4. maintenabilité ;
5. documentation pydoc ;
6. simplicité ;
7. performance raisonnable.

Ne privilégie pas une solution complexe si une solution simple, claire et testable suffit.
