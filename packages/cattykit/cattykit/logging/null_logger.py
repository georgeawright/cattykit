"""No-op model logger."""

from .event import ModelEvent


class NullLogger:
    """A logger that discards all events."""

    def log(self, event: ModelEvent) -> None:
        """Discard an event."""

    def close(self) -> None:
        """Release no resources."""
