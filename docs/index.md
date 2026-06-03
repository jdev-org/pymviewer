# pymviewer

`pymviewer` generates mviewer XML configuration files from QGIS Server
projects and WMS GetCapabilities documents.

## Install

```bash
python -m pip install pymviewer
```

For local development:

```bash
python -m pip install -e .
```

## CLI

Generate from a QGIS project:

```bash
pymviewer from-qgs \
  --project /path/to/project.qgs \
  --output /path/to/config.xml \
  --service-url http://localhost:90/ogc/data
```

Generate from a WMS GetCapabilities file:

```bash
pymviewer from-capabilities \
  --capabilities /path/to/GetCapabilities.xml \
  --output /path/to/config.xml \
  --service-url http://localhost:90/ogc/data
```

## Python API

```python
from pathlib import Path
from pymviewer.qgisxmviewer import create_mviewer_config_from_wms_capabilities

create_mviewer_config_from_wms_capabilities(
    Path("data_getcapabilities.xml"),
    Path("data.xml"),
    "http://localhost:90/ogc/data",
)
```

## Publish library

The repository publishes the package to PyPI from GitHub Actions when a GitHub
release is published.

PyPI project page: <https://pypi.org/project/pymviewer/>

### Prerequisites

- The workflow file is `.github/workflows/publish-pypi.yml`.
- PyPI Trusted Publishing must be configured for this GitHub repository.
- The version in `pyproject.toml` is used as the base version.
- The workflow publishes a derived version in the form
  `X.Y.Z.post<GITHUB_RUN_NUMBER>` to guarantee uniqueness on PyPI.

### Local build check

Before creating a release, build the package locally:

```bash
python -m pip install --upgrade build
python -m build
```

This produces the source distribution and wheel in `dist/`.

### Release flow

1. Update `version` in `pyproject.toml` if needed.
2. Commit and push the changes to GitHub.
3. Create a GitHub release from the tag you want to publish.
4. Publish the release in the GitHub UI.
5. GitHub Actions builds the package and uploads it to PyPI automatically.

### What the workflow does

At release publication time, GitHub Actions:

1. checks out the repository;
2. installs Python 3.12 and the `build` package;
3. rewrites `pyproject.toml` temporarily to append `.post<GITHUB_RUN_NUMBER>`
   to the configured version;
4. runs `python -m build`;
5. publishes the generated artifacts to PyPI with
   `pypa/gh-action-pypi-publish`.

## Build docs

Install the documentation dependencies:

```bash
python -m pip install -e ".[docs]"
```

Run the local documentation server:

```bash
mkdocs serve
```

Build the static site:

```bash
mkdocs build
```
