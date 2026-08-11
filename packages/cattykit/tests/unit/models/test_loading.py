from collections.abc import Mapping
from pathlib import Path
from typing import Any

import pytest
from cattykit.models import (
    ModelNotInstalledError,
    ModelPlugin,
    ModelRegistry,
    ModelSourceError,
    load_model,
    resolve_model_source,
)


class FakeModel:
    @property
    def name(self) -> str:
        return "fake"

    def solve(self, *args: Any, **kwargs: Any) -> dict[str, Any]:
        return {"ok": True}

    def close(self) -> None:
        pass


def factory(
    *,
    config: Mapping[str, Any] | None = None,
    **kwargs: Any,
) -> FakeModel:
    return FakeModel()


def test_load_model_uses_selected_registry() -> None:
    registry = ModelRegistry()
    registry.register(ModelPlugin(name="fake", factory=factory))

    model = load_model("fake", registry=registry)

    assert model.name == "fake"


def test_missing_official_model_has_installation_hint() -> None:
    registry = ModelRegistry()

    with pytest.raises(ModelNotInstalledError) as exc_info:
        load_model("copycat", registry=registry)

    message = str(exc_info.value)

    assert "cattykit.install_model('copycat')" in message


def test_model_name_resolves_through_the_model_source_map() -> None:
    kind, source = resolve_model_source(
        "fake",
        model_sources={"fake": "https://example.com/fake.whl"},
    )

    assert kind == "name"
    assert source == "https://example.com/fake.whl"


def test_https_url_is_used_directly() -> None:
    kind, source = resolve_model_source("https://example.com/fake.whl")

    assert kind == "url"
    assert source == "https://example.com/fake.whl"


def test_path_is_used_directly() -> None:
    kind, source = resolve_model_source(Path("models/copycat"))

    assert kind == "path"
    assert source == "models/copycat"


def test_unknown_name_is_rejected() -> None:
    with pytest.raises(ModelSourceError, match="No CattyKit model source"):
        resolve_model_source("unknown", model_sources={})
