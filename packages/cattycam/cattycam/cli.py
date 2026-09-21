"""Command-line launcher for the Cattycam web application."""

from __future__ import annotations

import argparse
from pathlib import Path

import panel as pn

from cattycam.application import create_app


def main() -> None:
    """Start Cattycam and open its database browser in a web browser."""
    parser = argparse.ArgumentParser(description="Browse a Cattycam SQLite database.")
    parser.add_argument(
        "database",
        type=Path,
        nargs="?",
        default="cattycam.sqlite",
        help="SQLite database to browse (default: cattycam.sqlite).",
    )
    args = parser.parse_args()

    pn.extension("tabulator")
    pn.serve(
        lambda: create_app(args.database),
        show=True,
        title="Cattycam",
    )
