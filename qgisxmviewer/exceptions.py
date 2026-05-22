"""Domain exceptions for QGIS project parsing and mviewer XML generation."""


class QgisProjectError(Exception):
    """Raised when a QGIS project cannot be read or interpreted."""


class MviewerXmlError(Exception):
    """Raised when a mviewer XML document cannot be generated."""
