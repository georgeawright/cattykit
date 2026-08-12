"""Structured events emitted by CattyKit models."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any


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
        return cls(timestamp=datetime.now(UTC), model=model, kind=kind, data=data)

    def as_dict(self) -> dict[str, Any]:
        """Return a JSON-ready representation of the event."""
        return {
            "timestamp": self.timestamp.isoformat(),
            "model": self.model,
            "kind": self.kind,
            "data": dict(self.data),
        }
