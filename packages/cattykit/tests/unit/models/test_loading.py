from collections.abc import Mapping
from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest
from cattykit.models import (
    ModelInstallationError,
    ModelNotInstalledError,
    ModelPlugin,
    ModelRegistry,
    ModelSourceError,
    install_model,
    load_model,
    resolve_model_source,
)


class FakeModel:
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

    assert model.solve() == {"ok": True}


def test_missing_official_model_has_installation_hint(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr("cattykit.models.registry.entry_points", lambda **_: ())
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


def test_install_model_explains_how_to_install_without_pip() -> None:
    with (
        patch("cattykit.models.loading.find_spec", return_value=None),
        patch("cattykit.models.loading.subprocess.run") as run,
    ):
        with pytest.raises(ModelInstallationError, match="does not include pip"):
            install_model("./models/copycat")

    run.assert_not_called()
