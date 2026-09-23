from __future__ import annotations

import json
import re
import subprocess
import sys
from collections.abc import Mapping
from importlib.util import find_spec
from pathlib import Path
from typing import Any, Literal
from urllib.parse import quote, unquote, urlparse
from urllib.request import Request, url2pathname, urlopen

from .protocol import CattyKitModel, ModelPlugin
from .registry import ModelRegistry, default_registry


class ModelNotInstalledError(LookupError):
    """Raised when a requested model plugin is not installed."""


class ModelSourceError(ValueError):
    """Raised when a model source cannot be interpreted."""


class ModelInstallationError(RuntimeError):
    """Raised when pip cannot install a model package."""


ModelSourceKind = Literal["name", "url", "path"]


_OFFICIAL_REPOSITORY = "https://github.com/georgeawright/cattykit.git"
_OFFICIAL_TAGS_URL = "https://api.github.com/repos/georgeawright/cattykit/tags"
_OFFICIAL_RELEASES_URL = "https://api.github.com/repos/georgeawright/cattykit/releases"
_RELEASE_TAG = re.compile(r"^(?P<name>.+)-v(?P<version>\d+\.\d+\.\d+)$", re.IGNORECASE)
_NEXT_PAGE_LINK = re.compile(r'<(?P<url>[^>]+)>;\s*rel="next"')


def resolve_model_source(
    source: str | Path,
    *,
    version: str | None = None,
    model_sources: Mapping[str, str] | None = None,
) -> tuple[ModelSourceKind, str]:
    """Classify a model source and resolve a model name to its package source.

    ``https://`` values are package URLs, while ``Path`` objects, ``file://``
    URLs, and explicit paths (for example ``./my-model``) are local sources.
    All other strings are treated as model names and looked up in
    ``model_sources``. Without a custom map, official names are discovered from
    GitHub release tags. ``version`` selects a specific official release.
    """
    if isinstance(source, Path):
        _reject_non_official_version(version)
        return "path", str(source.expanduser())

    parsed = urlparse(source)

    if parsed.scheme == "https" and parsed.netloc:
        _reject_non_official_version(version)
        return "url", source

    if parsed.scheme == "file":
        if parsed.netloc not in ("", "localhost"):
            raise ModelSourceError("Only local file URLs are supported.")
        _reject_non_official_version(version)
        return "path", url2pathname(unquote(parsed.path))

    if _is_explicit_path(source):
        _reject_non_official_version(version)
        return "path", str(Path(source).expanduser())

    if parsed.scheme:
        raise ModelSourceError(
            "Model URLs must use HTTPS; use a local path or file:// URL "
            "for local packages."
        )

    registered_source = (
        next(
            (
                (name, package_source)
                for name, package_source in model_sources.items()
                if name.casefold() == source.casefold()
            ),
            None,
        )
        if model_sources is not None
        else None
    )
    if registered_source is not None:
        name, package_source = registered_source
    elif model_sources is None:
        return "name", _official_release_source(source, version)
    else:
        raise ModelSourceError(
            f"No CattyKit model source is registered as {source!r}. "
            "Pass an HTTPS URL or an explicit local path instead."
        )

    if _is_official_source(package_source):
        package_source = _official_release_source(name, version)
    else:
        _reject_non_official_version(version)

    return "name", package_source


def install_model(
    source: str | Path,
    *,
    version: str | None = None,
    model_sources: Mapping[str, str] | None = None,
) -> None:
    """Install a CattyKit model package into the current Python environment.

    A name is resolved through the curated model-source map. Official names are
    installed from their matching GitHub release; ``version`` can select one.
    HTTPS URLs and explicit local paths are passed directly to pip.
    """
    _, package_source = resolve_model_source(
        source,
        version=version,
        model_sources=model_sources,
    )

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
        Registered model name.
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


def _reject_non_official_version(version: str | None) -> None:
    if version is not None:
        raise ModelSourceError(
            "A model version can only be selected for an official CattyKit model name."
        )


def _is_official_source(package_source: str) -> bool:
    return package_source.startswith(f"git+{_OFFICIAL_REPOSITORY}")


def _official_release_source(
    name: str,
    version: str | None,
) -> str:
    releases = []
    for tag in _github_tags():
        match = _RELEASE_TAG.fullmatch(tag)
        if match is None or match["name"].casefold() != name.casefold():
            continue
        if version is not None and match["version"].casefold() != version.casefold():
            continue
        releases.append((tuple(map(int, match["version"].split("."))), tag))

    if not releases:
        requested = f" version {version!r}" if version is not None else ""
        raise ModelSourceError(
            f"No official GitHub release found for model {name!r}{requested}."
        )

    tag = max(releases)[1]
    return _github_release_wheel(tag)


def _github_tags() -> tuple[str, ...]:
    url = f"{_OFFICIAL_TAGS_URL}?per_page=100"
    tags: list[str] = []

    while url:
        request = Request(url, headers={"Accept": "application/vnd.github+json"})
        try:
            with urlopen(request) as response:  # noqa: S310 - fixed GitHub API endpoint
                payload = json.load(response)
                link_header = response.headers.get("Link", "")
        except OSError as error:
            raise ModelSourceError(
                "Could not retrieve official CattyKit GitHub releases."
            ) from error

        if not isinstance(payload, list):
            raise ModelSourceError(
                "Could not interpret official CattyKit GitHub releases."
            )

        tags.extend(
            tag["name"]
            for tag in payload
            if isinstance(tag, dict) and isinstance(tag.get("name"), str)
        )
        next_page = _NEXT_PAGE_LINK.search(link_header)
        url = next_page["url"] if next_page is not None else ""

    return tuple(tags)


def _github_release_wheel(tag: str) -> str:
    request = Request(
        f"{_OFFICIAL_RELEASES_URL}/tags/{quote(tag, safe='')}",
        headers={"Accept": "application/vnd.github+json"},
    )
    try:
        with urlopen(request) as response:  # noqa: S310 - fixed GitHub API endpoint
            payload = json.load(response)
    except OSError as error:
        raise ModelSourceError(
            f"Could not retrieve the official CattyKit GitHub release for tag {tag!r}."
        ) from error

    if not isinstance(payload, dict):
        raise ModelSourceError(
            f"Could not interpret the official CattyKit GitHub release for tag {tag!r}."
        )

    wheels = [
        asset["browser_download_url"]
        for asset in payload.get("assets", [])
        if isinstance(asset, dict)
        and isinstance(asset.get("browser_download_url"), str)
        and asset["browser_download_url"].lower().endswith(".whl")
    ]
    if len(wheels) != 1:
        raise ModelSourceError(
            f"Official CattyKit GitHub release {tag!r} must contain exactly one wheel."
        )
    return wheels[0]
