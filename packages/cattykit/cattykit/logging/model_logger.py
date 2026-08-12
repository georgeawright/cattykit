"""Protocol implemented by CattyKit loggers."""

from typing import Protocol, runtime_checkable

from .event import ModelEvent


@runtime_checkable
class ModelLogger(Protocol):
    """Receives structured events emitted by a model."""

    def log(self, event: ModelEvent) -> None:
        """Record an event."""
        ...

    def close(self) -> None:
        """Release logger resources."""
        ...
