"""JSON-lines model logger."""

import json
import sys
from typing import TextIO

from .event import ModelEvent


class PrintLogger:
    """A logger that writes one JSON event per line to a text stream."""

    def __init__(self, stream: TextIO | None = None) -> None:
        self._stream = stream if stream is not None else sys.stdout

    def log(self, event: ModelEvent) -> None:
        """Print an event as a JSON line."""
        print(
            json.dumps(event.as_dict(), sort_keys=True), file=self._stream, flush=True
        )

    def close(self) -> None:
        """Flush, but do not close, the caller-owned stream."""
        self._stream.flush()
