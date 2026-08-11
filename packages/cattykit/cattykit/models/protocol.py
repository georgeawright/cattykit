from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class CattyKitModel(Protocol):
    """Minimum interface implemented by a runnable CattyKit model."""

    def solve(self, *args: Any, **kwargs: Any) -> Any:
        """Run the model and return its result."""
        ...

    def close(self) -> None:
        """Release resources owned by the model."""
        ...


@runtime_checkable
class ModelFactory(Protocol):
    """Callable used to construct a model plugin."""

    def __call__(
        self,
        *,
        config: Mapping[str, Any] | None = None,
        **kwargs: Any,
    ) -> CattyKitModel:
        ...


@dataclass(frozen=True, slots=True)
class ModelPlugin:
    """Description of an installed CattyKit model plugin."""

    name: str
    factory: ModelFactory
    version: str | None = None
    description: str | None = None

    def create(
        self,
        *,
        config: Mapping[str, Any] | None = None,
        **kwargs: Any,
    ) -> CattyKitModel:
        """Construct a model using this plugin's factory."""
        model = self.factory(config=config, **kwargs)

        if not isinstance(model, CattyKitModel):
            raise TypeError(
                f"Factory for model {self.name!r} returned "
                f"{type(model).__name__}, which does not satisfy "
                "the CattyKitModel protocol."
            )

        return model
