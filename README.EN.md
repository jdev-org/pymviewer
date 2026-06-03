# pymviewer

`pymviewer` generates mviewer XML configuration files from QGIS Server
projects and WMS GetCapabilities documents.

## Install

```bash
python -m pip install -e qgisxmviewer
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

PyPI project page: https://pypi.org/project/pymviewer/

### Prerequisites

- The workflow file is
  [.github/workflows/publish-pypi.yml](/home/gaetan/projects/mviewer/pymviewer/.github/workflows/publish-pypi.yml).
- PyPI Trusted Publishing must be configured for this GitHub repository.
- The version in `pyproject.toml` is used as the base version.
- The workflow publishes a derived version in the form
  `X.Y.Z.post<GITHUB_RUN_NUMBER>` to guarantee uniqueness on PyPI.
- Build-time tooling is listed in
  [requirements.txt](/home/gaetan/projects/mviewer/pymviewer/requirements.txt).

### Local build check

Before creating a release, build the package locally:

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
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

### Manual notes

- The published PyPI version will not exactly match the GitHub tag if the
  `.post...` suffix is added by the workflow.
- If exact tag-to-version parity is required, the workflow must be adjusted to
  publish the exact tag version instead of generating a post-release suffix.

## Docs

The project ships a `mkdocs-material` configuration in
[mkdocs.yml](/home/gaetan/projects/mviewer/pymviewer/mkdocs.yml) with the
source pages in [docs/index.md](/home/gaetan/projects/mviewer/pymviewer/docs/index.md).

The published documentation is intended to be available on GitHub Pages:
<https://jdev-org.github.io/pymviewer/>

Build and documentation dependencies are centralized in
[requirements.txt](/home/gaetan/projects/mviewer/pymviewer/requirements.txt).

Install the documentation and build dependencies:

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

The shared `requirements.txt` currently includes `build`, `mkdocs-material`,
and `black`.

Format the codebase with:

```bash
black .
```

Run the local documentation server:

```bash
mkdocs serve
```

Build the static documentation site:

```bash
mkdocs build
```

GitHub Pages deployment is handled by
[deploy-docs.yml](/home/gaetan/projects/mviewer/pymviewer/.github/workflows/deploy-docs.yml)
on each push to `main`.

To enable it in GitHub:

1. Open the repository settings.
2. Go to `Pages`.
3. Set the source to `GitHub Actions`.

## Notes

- mviewer layer `id` values are normalized and unique.
- WMS layer names are preserved in the `layers` attribute.
- WMS legend URLs are encoded and can be rebased to an override service URL.
- `.qgs` projects are supported. `.qgz` archives are not supported yet.
