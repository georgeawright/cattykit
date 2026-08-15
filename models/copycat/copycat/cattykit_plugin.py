"""CattyKit plugin integration for Copycat."""

from __future__ import annotations

import random
from collections.abc import Mapping
from importlib.resources import as_file, files
from pathlib import Path
from typing import Any, cast

from cattykit.logging import ModelLogger
from cattykit.models import ModelPlugin

from .copycat import Copycat

_CONFIG_DIRECTORY = files("copycat").joinpath("configs")


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
    logger: ModelLogger | None = None,
    **kwargs: Any,
) -> Copycat:
    """Create a Copycat model from its bundled configuration files."""
    options = dict(config or {})
    config_directory = options.pop("config_directory", None)
    seed = options.pop("seed", None)

    if options:
        unexpected = ", ".join(sorted(options))
        raise TypeError(f"Unsupported Copycat configuration option(s): {unexpected}.")

    if seed is not None:
        random.seed(seed)

    if config_directory is not None:
        return _load_copycat(Path(config_directory), logger)

    with as_file(_CONFIG_DIRECTORY) as bundled_config_directory:
        return _load_copycat(bundled_config_directory, logger)


def _load_copycat(config_directory: Path, logger: ModelLogger | None) -> Copycat:
    """Load Copycat from a directory containing its JSON configuration files."""
    return cast(
        Copycat,
        Copycat.from_json(
            str(config_directory / "slipnet.json"),
            str(config_directory / "coderack.json"),
            str(config_directory / "hyperparameters.json"),
            logger=logger,
        ),
    )
