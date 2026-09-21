"""No-op model logger."""

from .identifiers import LoggerIdentifiers


class NullLogger(LoggerIdentifiers):
    """A logger that discards all events."""

    def __init__(self, model_name: str) -> None:
        self.model_name = model_name

    def log(self, kind: str, **data: object) -> None:
        """Discard an event."""

    def close(self) -> None:
        """Release no resources."""
