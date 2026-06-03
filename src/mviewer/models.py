"""Internal data models related to mviewer serialization."""

from dataclasses import dataclass


@dataclass(frozen=True)
class MviewerLayer:
    """Represent a layer ready to be serialized as mviewer XML."""

    id: str
    name: str
    layer_type: str
    url: str | None
    layers: str | None
    visible: bool
    queryable: bool
    group: str | None
