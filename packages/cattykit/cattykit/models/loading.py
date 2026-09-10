from __future__ import annotations

import subprocess
import sys
from collections.abc import Mapping
from importlib.util import find_spec
from pathlib import Path
from typing import Any, Literal
from urllib.parse import unquote, urlparse
from urllib.request import url2pathname

from .protocol import CattyKitModel, ModelPlugin
from .registry import ModelRegistry, default_registry


class ModelNotInstalledError(LookupError):
    """Raised when a requested model plugin is not installed."""


class ModelSourceError(ValueError):
    """Raised when a model source cannot be interpreted."""


class ModelInstallationError(RuntimeError):
    """Raised when pip cannot install a model package."""


ModelSourceKind = Literal["name", "url", "path"]


OFFICIAL_MODEL_SOURCES: dict[str, str] = {
    "copycat": (
        "git+https://github.com/georgeawright/cattykit.git"
        "#subdirectory=models/copycat"
    ),
}


def resolve_model_source(
    source: str | Path,
    *,
    model_sources: Mapping[str, str] = OFFICIAL_MODEL_SOURCES,
) -> tuple[ModelSourceKind, str]:
    """Classify a model source and resolve a model name to its package source.

    ``https://`` values are package URLs, while ``Path`` objects, ``file://``
    URLs, and explicit paths (for example ``./copycat``) are local sources.
    All other strings are treated as model names and looked up in
    ``model_sources``.
    """
    if isinstance(source, Path):
        return "path", str(source.expanduser())

    parsed = urlparse(source)

    if parsed.scheme == "https" and parsed.netloc:
        return "url", source

    if parsed.scheme == "file":
        if parsed.netloc not in ("", "localhost"):
            raise ModelSourceError("Only local file URLs are supported.")
        return "path", url2pathname(unquote(parsed.path))

    if _is_explicit_path(source):
        return "path", str(Path(source).expanduser())

    if parsed.scheme:
        raise ModelSourceError(
            "Model URLs must use HTTPS; use a local path or file:// URL "
            "for local packages."
        )

    try:
        return "name", model_sources[source]
    except KeyError as error:
        raise ModelSourceError(
            f"No CattyKit model source is registered as {source!r}. "
            "Pass an HTTPS URL or an explicit local path instead."
        ) from error


def install_model(
    source: str | Path,
    *,
    model_sources: Mapping[str, str] = OFFICIAL_MODEL_SOURCES,
) -> None:
    """Install a CattyKit model package into the current Python environment.

    A name is resolved through the curated model-source map. HTTPS URLs and
    explicit local paths are passed directly to pip.
    """
    _, package_source = resolve_model_source(source, model_sources=model_sources)

    if find_spec("pip") is None:
        raise ModelInstallationError(
            "The active Python environment does not include pip. "
            "Install the model with your environment manager instead, for example: "
            f"uv pip install {package_source}"
        )

    try:
        subprocess.run(
            [sys.executable, "-m", "pip", "install", package_source],
            check=True,
        )
    except subprocess.CalledProcessError as error:
        raise ModelInstallationError(
            f"Could not install CattyKit model from {package_source!r}."
        ) from error


def available_models(
    *,
    registry: ModelRegistry = default_registry,
) -> tuple[str, ...]:
    """Return the names of all installed CattyKit models."""
    return registry.names()


def model_info(
    name: str,
    *,
    registry: ModelRegistry = default_registry,
) -> ModelPlugin:
    """Return metadata and the factory for an installed model."""
    try:
        return registry.get(name)
    except KeyError as error:
        raise _model_not_installed_error(
            name,
            installed=registry.names(),
        ) from error


def load_model(
    name: str,
    *,
    config: Mapping[str, Any] | None = None,
    registry: ModelRegistry = default_registry,
    **kwargs: Any,
) -> CattyKitModel:
    """Construct an installed CattyKit model.

    Parameters
    ----------
    name:
        Registered model name, such as ``"copycat"``.
    config:
        Optional model-specific configuration.
    registry:
        Registry to use. Primarily useful for testing.
    **kwargs:
        Additional model-specific factory arguments.
    """
    plugin = model_info(name, registry=registry)
    return plugin.create(config=config, **kwargs)


def _model_not_installed_error(
    name: str,
    *,
    installed: tuple[str, ...],
) -> ModelNotInstalledError:
    installed_text = ", ".join(installed) if installed else "none"

    lines = [
        f"CattyKit model {name!r} is not installed.",
        f"Installed models: {installed_text}.",
    ]

    source = OFFICIAL_MODEL_SOURCES.get(name)

    if source is not None:
        lines.extend(
            [
                "",
                "Install the official model with:",
                f"    python -c \"import cattykit; cattykit.install_model('{name}')\"",
            ]
        )

    return ModelNotInstalledError("\n".join(lines))


def _is_explicit_path(value: str) -> bool:
    return value.startswith(("./", "../", "~/", "/")) or "/" in value
