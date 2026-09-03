"""Panel application for browsing a Cattycam SQLite database.

Run with ``panel serve cattycam/app.py --show --args path/to/history.sqlite``.
"""

from __future__ import annotations

import sys
from pathlib import Path

import panel as pn

# Panel executes a served file as a script, rather than as a package module.
# Add the source-package root so this works with ``panel serve cattycam/app.py``.
PACKAGE_ROOT = Path(__file__).resolve().parent.parent
if str(PACKAGE_ROOT) not in sys.path:
    sys.path.insert(0, str(PACKAGE_ROOT))

from cattycam.application import create_app

pn.extension("tabulator")

database_argument = sys.argv[1] if len(sys.argv) > 1 else "cattycam.sqlite"
create_app(database_argument).servable(title="Cattycam")
