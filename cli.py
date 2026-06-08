"""Command-line interface for pymviewer."""

from pathlib import Path
import argparse
import logging

from qgisxmviewer.services.qgis_to_mviewer import (
    create_mviewer_config_from_qgis_project,
    create_mviewer_config_from_wms_capabilities,
)


def build_parser() -> argparse.ArgumentParser:
    """Build the CLI argument parser."""
    parser = argparse.ArgumentParser(
        prog="pymviewer",
        description="Generate mviewer XML from QGIS Server sources.",
    )
    parser.add_argument("--log-level", default="INFO", help="Python logging level")
    subparsers = parser.add_subparsers(dest="command", required=True)

    from_qgs = subparsers.add_parser(
        "from-qgs", help="Generate XML from a QGIS .qgs file"
    )
    from_qgs.add_argument(
        "--project", required=True, type=Path, help="Path to the QGIS .qgs file"
    )
    from_qgs.add_argument("--output", required=True, type=Path, help="Output XML path")
    from_qgs.add_argument(
        "--service-url", required=True, help="QGIS Server WMS base URL"
    )

    from_capabilities = subparsers.add_parser(
        "from-capabilities",
        help="Generate XML from a WMS GetCapabilities file",
    )
    from_capabilities.add_argument(
        "--capabilities",
        required=True,
        type=Path,
        help="Path to the WMS GetCapabilities XML file",
    )
    from_capabilities.add_argument(
        "--output", required=True, type=Path, help="Output XML path"
    )
    from_capabilities.add_argument(
        "--service-url", help="Override WMS service base URL"
    )
    return parser


def main() -> int:
    """Run the command-line interface."""
    parser = build_parser()
    args = parser.parse_args()
    logging.basicConfig(level=getattr(logging, args.log_level.upper(), logging.INFO))

    if args.command == "from-qgs":
        output = create_mviewer_config_from_qgis_project(
            args.project,
            args.output,
            args.service_url,
        )
    elif args.command == "from-capabilities":
        output = create_mviewer_config_from_wms_capabilities(
            args.capabilities,
            args.output,
            args.service_url,
        )
    else:
        parser.error(f"Unsupported command: {args.command}")
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
