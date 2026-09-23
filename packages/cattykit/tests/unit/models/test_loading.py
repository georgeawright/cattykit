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


def test_model_name_lookup_is_case_insensitive() -> None:
    kind, source = resolve_model_source(
        "FAKE",
        model_sources={"fake": "https://example.com/fake.whl"},
    )

    assert kind == "name"
    assert source == "https://example.com/fake.whl"


@patch(
    "cattykit.models.loading._github_tags",
    return_value=("copycat-v0.1.0", "COPYCAT-v0.2.0", "cattycam-v1.0.0"),
)
@patch(
    "cattykit.models.loading._github_release_wheel",
    return_value="https://example.com/releases/COPYCAT-v0.2.0/copycat-0.2.0.whl",
)
def test_official_model_resolves_to_its_latest_github_release(
    github_release_wheel: Any,
    github_tags: Any,
) -> None:
    kind, source = resolve_model_source("CopyCat")

    assert kind == "name"
    assert source == "https://example.com/releases/COPYCAT-v0.2.0/copycat-0.2.0.whl"
    github_tags.assert_called_once_with()
    github_release_wheel.assert_called_once_with("COPYCAT-v0.2.0")


@patch(
    "cattykit.models.loading._github_tags",
    return_value=("copycat-v0.1.0", "copycat-v0.2.0"),
)
@patch(
    "cattykit.models.loading._github_release_wheel",
    return_value="https://example.com/releases/copycat-v0.1.0/copycat-0.1.0.whl",
)
def test_official_model_version_selects_matching_github_release(
    github_release_wheel: Any,
    github_tags: Any,
) -> None:
    _, source = resolve_model_source("COPYCAT", version="0.1.0")

    assert source == "https://example.com/releases/copycat-v0.1.0/copycat-0.1.0.whl"
    github_tags.assert_called_once_with()
    github_release_wheel.assert_called_once_with("copycat-v0.1.0")


@patch(
    "cattykit.models.loading._github_tags",
    return_value=("cattycam-v1.0.0",),
)
@patch(
    "cattykit.models.loading._github_release_wheel",
    return_value="https://example.com/releases/cattycam-v1.0.0/cattycam-1.0.0.whl",
)
def test_unregistered_official_model_is_discovered_from_its_release_tag(
    github_release_wheel: Any,
    github_tags: Any,
) -> None:
    _, source = resolve_model_source("CaTtYcAm")

    assert source == "https://example.com/releases/cattycam-v1.0.0/cattycam-1.0.0.whl"
    github_tags.assert_called_once_with()
    github_release_wheel.assert_called_once_with("cattycam-v1.0.0")


def test_version_is_rejected_for_non_official_sources() -> None:
    with pytest.raises(ModelSourceError, match="only be selected"):
        resolve_model_source("https://example.com/fake.whl", version="1.0.0")


@patch(
    "cattykit.models.loading.resolve_model_source",
    return_value=("name", "https://example.com/fake.whl"),
)
@patch("cattykit.models.loading.find_spec", return_value=object())
@patch("cattykit.models.loading.subprocess.run")
def test_install_model_passes_version_to_source_resolution(
    run: Any,
    _: Any,
    resolve: Any,
) -> None:
    install_model("copycat", version="0.1.0")

    resolve.assert_called_once_with(
        "copycat",
        version="0.1.0",
        model_sources=None,
    )
    run.assert_called_once()


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
