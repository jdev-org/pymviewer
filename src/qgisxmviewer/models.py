"""Internal data models used by the QGIS parsing workflow."""

from dataclasses import dataclass, field


@dataclass(frozen=True)
class QgisExtent:
    """Represent a layer bounding box extracted from a QGIS project."""

    xmin: float | None = None
    ymin: float | None = None
    xmax: float | None = None
    ymax: float | None = None


@dataclass(frozen=True)
class QgisLayer:
    """Represent a layer extracted from a QGIS project."""

    id: str
    name: str
    title: str | None
    provider: str | None
    source: str | None
    layer_type: str
    group: str | None
    visible: bool
    crs: str | None
    abstract: str | None = None
    extent: QgisExtent | None = None
    published_name: str | None = None
    short_name: str | None = None
    queryable: bool = True
    wms_published: bool = True
    wfs_published: bool = False
    xyz: bool = False
    legend_url: str | None = None
    metadata: dict[str, str] = field(default_factory=dict)
