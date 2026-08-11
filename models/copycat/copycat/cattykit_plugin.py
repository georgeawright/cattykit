"""CattyKit plugin integration for Copycat."""

from __future__ import annotations

import random
import sysconfig
from collections.abc import Mapping
from pathlib import Path
from typing import Any, cast

from cattykit.models import ModelPlugin

from .copycat import Copycat

_INSTALLED_CONFIG_DIRECTORY = Path(sysconfig.get_path("data")) / "copycat" / "configs"
_SOURCE_CONFIG_DIRECTORY = Path(__file__).parent.parent / "configs"
_CONFIG_DIRECTORY = (
    _INSTALLED_CONFIG_DIRECTORY
    if _INSTALLED_CONFIG_DIRECTORY.is_dir()
    else _SOURCE_CONFIG_DIRECTORY
)


def plugin() -> ModelPlugin:
    """Return the descriptor exposed through the ``cattykit.models`` entry point."""
    return ModelPlugin(
        name="copycat",
        version="0.1.0",
        description="A Python implementation of the Copycat analogy-making model.",
        factory=create_model,
    )


def create_model(
    *,
    config: Mapping[str, Any] | None = None,
    **kwargs: Any,
) -> Copycat:
    """Create a Copycat model from its bundled configuration files."""
    options = dict(config or {})
    config_directory = Path(options.pop("config_directory", _CONFIG_DIRECTORY))
    seed = options.pop("seed", None)

    if options:
        unexpected = ", ".join(sorted(options))
        raise TypeError(f"Unsupported Copycat configuration option(s): {unexpected}.")

    if seed is not None:
        random.seed(seed)

    return cast(
        Copycat,
        Copycat.from_json(
            str(config_directory / "slipnet.json"),
            str(config_directory / "coderack.json"),
            str(config_directory / "hyperparameters.json"),
        ),
    )
