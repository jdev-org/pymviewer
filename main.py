"""Command-line entry point for QGIS project to mviewer XML conversion."""

from pathlib import Path
import argparse
import logging
import sys

sys.path.insert(
    0, str(Path(__file__).resolve().parent / "lib" / "qgisxmviewer" / "src")
)

from qgisxmviewer.services.qgis_to_mviewer import (
    create_mviewer_config_from_qgis_project,
)


def build_parser() -> argparse.ArgumentParser:
    """Build the command-line argument parser."""
    parser = argparse.ArgumentParser(
        description="Generate a mviewer XML configuration from a QGIS Server project."
    )
    parser.add_argument(
        "--project", required=True, type=Path, help="Path to the QGIS .qgs project"
    )
    parser.add_argument(
        "--output", required=True, type=Path, help="Output mviewer XML path"
    )
    parser.add_argument("--service-url", required=True, help="QGIS Server base URL")
    parser.add_argument("--log-level", default="INFO", help="Python logging level")
    return parser


def main() -> int:
    """Run the CLI workflow."""
    parser = build_parser()
    args = parser.parse_args()
    logging.basicConfig(level=getattr(logging, args.log_level.upper(), logging.INFO))
    output = create_mviewer_config_from_qgis_project(
        args.project, args.output, args.service_url
    )
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
