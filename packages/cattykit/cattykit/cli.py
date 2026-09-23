from __future__ import annotations

import argparse
from collections.abc import Sequence

from .models import ModelInstallationError, ModelSourceError, install_model


def main(argv: Sequence[str] | None = None) -> None:
    """Run the CattyKit command-line interface."""
    parser = argparse.ArgumentParser(prog="cattykit")
    commands = parser.add_subparsers(dest="command", required=True)

    install_parser = commands.add_parser("install", help="Install a model.")
    install_parser.add_argument(
        "source", help="Official model name, HTTPS URL, or local path."
    )
    install_parser.add_argument(
        "--version",
        help="Official model version to install.",
    )

    args = parser.parse_args(argv)

    try:
        install_model(args.source, version=args.version)
    except (ModelInstallationError, ModelSourceError) as error:
        parser.error(str(error))
