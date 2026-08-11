from collections.abc import Mapping
from typing import Any

from cattykit.models import ModelPlugin, ModelRegistry


class FakeModel:
    def solve(self, *args: Any, **kwargs: Any) -> str:
        return "result"

    def close(self) -> None:
        pass


def create_fake_model(
    *,
    config: Mapping[str, Any] | None = None,
    **kwargs: Any,
) -> FakeModel:
    return FakeModel()


def test_directly_registered_model_can_be_loaded() -> None:
    registry = ModelRegistry()
    registry.register(
        ModelPlugin(
            name="fake",
            version="1.0",
            factory=create_fake_model,
        )
    )

    plugin = registry.get("fake")
    model = plugin.create()

    assert model.solve() == "result"
