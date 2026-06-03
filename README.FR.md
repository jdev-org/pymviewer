# pymviewer

`pymviewer` génère des fichiers de configuration XML mviewer à partir de
projets QGIS Server et de documents WMS GetCapabilities.

## Installation

```bash
python -m pip install -e qgisxmviewer
```

## CLI

Générer depuis un projet QGIS :

```bash
pymviewer from-qgs \
  --project /path/to/project.qgs \
  --output /path/to/config.xml \
  --service-url http://localhost:90/ogc/data
```

Générer depuis un fichier WMS GetCapabilities :

```bash
pymviewer from-capabilities \
  --capabilities /path/to/GetCapabilities.xml \
  --output /path/to/config.xml \
  --service-url http://localhost:90/ogc/data
```

## API Python

```python
from pathlib import Path
from pymviewer.qgisxmviewer import create_mviewer_config_from_wms_capabilities

create_mviewer_config_from_wms_capabilities(
    Path("data_getcapabilities.xml"),
    Path("data.xml"),
    "http://localhost:90/ogc/data",
)
```

## Publication de la librairie

Le dépôt publie le package sur PyPI via GitHub Actions lorsqu’une GitHub
release est publiée.

Page du projet PyPI : https://pypi.org/project/pymviewer/

### Prérequis

- Le workflow utilisé est
  [.github/workflows/publish-pypi.yml](/home/gaetan/projects/mviewer/pymviewer/.github/workflows/publish-pypi.yml).
- PyPI Trusted Publishing doit être configuré pour ce dépôt GitHub.
- La version définie dans `pyproject.toml` sert de version de base.
- Le workflow publie une version dérivée sous la forme
  `X.Y.Z.post<GITHUB_RUN_NUMBER>` pour garantir l’unicité sur PyPI.
- Les outils de build sont listés dans
  [requirements.txt](/home/gaetan/projects/mviewer/pymviewer/requirements.txt).

### Vérification locale du build

Avant de créer une release, construis le package localement :

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m build
```

Cela produit la source distribution et la wheel dans `dist/`.

### Flux de release

1. Mettre à jour `version` dans `pyproject.toml` si nécessaire.
2. Committer et pousser les changements vers GitHub.
3. Créer une GitHub release à partir du tag à publier.
4. Publier la release dans l’interface GitHub.
5. GitHub Actions construit le package et le publie automatiquement sur PyPI.

### Ce que fait le workflow

Au moment de la publication d’une release, GitHub Actions :

1. récupère le dépôt ;
2. installe Python 3.12 et le package `build` ;
3. réécrit temporairement `pyproject.toml` pour ajouter
   `.post<GITHUB_RUN_NUMBER>` à la version configurée ;
4. exécute `python -m build` ;
5. publie les artefacts générés sur PyPI avec
   `pypa/gh-action-pypi-publish`.

### Notes manuelles

- La version publiée sur PyPI ne correspondra pas exactement au tag GitHub si
  le suffixe `.post...` est ajouté par le workflow.
- Si tu veux une stricte correspondance entre tag et version, il faut adapter
  le workflow pour publier exactement la version du tag.

## Documentation

Le projet fournit une configuration `mkdocs-material` dans
[mkdocs.yml](/home/gaetan/projects/mviewer/pymviewer/mkdocs.yml), avec les
pages sources dans [docs/index.md](/home/gaetan/projects/mviewer/pymviewer/docs/index.md).

La documentation publiée est prévue pour être disponible sur GitHub Pages :
<https://jdev-org.github.io/pymviewer/>

Les dépendances de build et de documentation sont centralisées dans
[requirements.txt](/home/gaetan/projects/mviewer/pymviewer/requirements.txt).

Installer les dépendances de documentation et de build :

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Le fichier `requirements.txt` partagé contient actuellement `build`,
`mkdocs-material` et `black`.

Formater le code avec :

```bash
black .
```

Lancer le serveur local de documentation :

```bash
mkdocs serve
```

Construire le site statique de documentation :

```bash
mkdocs build
```

Le déploiement GitHub Pages est géré par
[deploy-docs.yml](/home/gaetan/projects/mviewer/pymviewer/.github/workflows/deploy-docs.yml)
à chaque push sur `main`.

Pour l’activer dans GitHub :

1. Ouvrir les paramètres du dépôt.
2. Aller dans `Pages`.
3. Choisir `GitHub Actions` comme source.

## Notes

- Les `id` de couches mviewer sont normalisés et uniques.
- Les noms de couches WMS sont conservés dans l’attribut `layers`.
- Les URLs de légende WMS sont encodées et peuvent être rebasées sur une URL
  de service surchargée.
- Les projets `.qgs` sont pris en charge. Les archives `.qgz` ne le sont pas
  encore.
