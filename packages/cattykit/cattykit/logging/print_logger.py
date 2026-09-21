"""JSON-lines model logger."""

import json
import sys
from datetime import UTC, datetime
from typing import TextIO

from .identifiers import LoggerIdentifiers


class PrintLogger(LoggerIdentifiers):
    """A logger that writes one JSON event per line to a text stream."""

    def __init__(self, model_name: str, stream: TextIO | None = None) -> None:
        self.model_name = model_name
        self._stream = stream if stream is not None else sys.stdout

    def log(self, kind: str, **data: object) -> None:
        """Print an event as a JSON line."""
        print(
            json.dumps(
                {
                    "timestamp": datetime.now(UTC).isoformat(),
                    "model": self.model_name,
                    "kind": kind,
                    "data": self.event_data(kind, data),
                },
                sort_keys=True,
            ),
            file=self._stream,
            flush=True,
        )

    def close(self) -> None:
        """Flush, but do not close, the caller-owned stream."""
        self._stream.flush()
