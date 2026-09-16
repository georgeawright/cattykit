"""Protocol implemented by CattyKit loggers."""

from typing import Protocol, runtime_checkable

@runtime_checkable
class ModelLogger(Protocol):
    """Receives structured events emitted by a model."""

    def log(self, kind: str, **data: object) -> None:
        """Record an event."""
        ...

    def close(self) -> None:
        """Release logger resources."""
        ...
