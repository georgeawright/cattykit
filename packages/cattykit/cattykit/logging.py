"""Structured event logging for CattyKit model runs."""

from __future__ import annotations

import json
import sqlite3
import sys
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Protocol, TextIO, runtime_checkable


@dataclass(frozen=True, slots=True)
class ModelEvent:
    """A structured event emitted during a model run."""

    timestamp: datetime
    model: str
    kind: str
    data: Mapping[str, Any]

    @classmethod
    def create(cls, model: str, kind: str, **data: Any) -> ModelEvent:
        """Create an event timestamped in UTC."""
        return cls(
            timestamp=datetime.now(UTC),
            model=model,
            kind=kind,
            data=data,
        )

    def as_dict(self) -> dict[str, Any]:
        """Return a JSON-ready representation of the event."""
        return {
            "timestamp": self.timestamp.isoformat(),
            "model": self.model,
            "kind": self.kind,
            "data": dict(self.data),
        }


@runtime_checkable
class ModelLogger(Protocol):
    """Receives structured events emitted by a model."""

    def log(self, event: ModelEvent) -> None:
        """Record an event."""
        ...

    def close(self) -> None:
        """Release logger resources."""
        ...


class NullLogger:
    """A logger that discards all events."""

    def log(self, event: ModelEvent) -> None:
        """Discard an event."""

    def close(self) -> None:
        """Release no resources."""


class PrintLogger:
    """A logger that writes one JSON event per line to a text stream."""

    def __init__(self, stream: TextIO | None = None) -> None:
        self._stream = stream if stream is not None else sys.stdout

    def log(self, event: ModelEvent) -> None:
        """Print an event as a JSON line."""
        print(
            json.dumps(event.as_dict(), sort_keys=True),
            file=self._stream,
            flush=True,
        )

    def close(self) -> None:
        """Flush, but do not close, the caller-owned stream."""
        self._stream.flush()


class SQLiteLogger:
    """A logger that persists structured events in a SQLite database."""

    def __init__(self, path: str | Path) -> None:
        self._connection = sqlite3.connect(path)
        self._connection.execute(
            """
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY,
                timestamp TEXT NOT NULL,
                model TEXT NOT NULL,
                kind TEXT NOT NULL,
                data_json TEXT NOT NULL
            )
            """
        )
        self._connection.commit()

    def log(self, event: ModelEvent) -> None:
        """Insert an event and commit it immediately."""
        self._connection.execute(
            """
            INSERT INTO events (timestamp, model, kind, data_json)
            VALUES (?, ?, ?, ?)
            """,
            (
                event.timestamp.isoformat(),
                event.model,
                event.kind,
                json.dumps(event.data, sort_keys=True),
            ),
        )
        self._connection.commit()

    def close(self) -> None:
        """Close the SQLite connection."""
        self._connection.close()
