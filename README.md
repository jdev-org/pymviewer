# pymviewer

`pymviewer` generates mviewer XML configuration files from QGIS Server
projects and WMS GetCapabilities documents.

## Install

```bash
python -m pip install -e python/lib/qgisxmviewer
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

## Notes

- mviewer layer `id` values are normalized and unique.
- WMS layer names are preserved in the `layers` attribute.
- WMS legend URLs are encoded and can be rebased to an override service URL.
- `.qgs` projects are supported. `.qgz` archives are not supported yet.
