"""Configure a copy of the original Metacat loader."""

import re
import sys
from pathlib import Path

source, destination = map(Path, sys.argv[1:])
settings = {
    "*platform*": "'linux",
    "*metacat-directory*": '"/opt/Metacat/"',
    "*file-dialog-directory*": '"/results/"',
    "*tcl/tk-version*": "8.6",
}
loader = source.read_text(encoding="utf-8")
for name, value in settings.items():
    pattern = rf"^(?:;; )?\(define {re.escape(name)} .+$"
    loader, count = re.subn(pattern, "", loader, flags=re.MULTILINE)
    if count == 0:
        raise ValueError(f"Missing {name} in {source}")
    loader = f"(define {name} {value})\n{loader}"
destination.write_text(loader, encoding="utf-8")
