from __future__ import annotations

from collections.abc import Iterable
from importlib.metadata import EntryPoint, entry_points
from typing import Final

from .protocol import ModelPlugin

ENTRY_POINT_GROUP: Final = "cattykit.models"


class ModelRegistryError(RuntimeError):
    """Base exception for model-registry failures."""


class DuplicateModelError(ModelRegistryError):
    """Raised when more than one plugin uses the same model name."""


class InvalidModelPluginError(ModelRegistryError):
    """Raised when an entry point does not provide a valid plugin."""


class ModelRegistry:
    """Registry of installed and explicitly registered CattyKit models."""

    def __init__(self) -> None:
        self._plugins: dict[str, ModelPlugin] = {}
        self._discovered = False

    def register(
        self,
        plugin: ModelPlugin,
        *,
        replace: bool = False,
    ) -> None:
        """Register a plugin directly.

        Direct registration is useful for tests and locally defined models.
        """
        self._validate_name(plugin.name)

        if plugin.name in self._plugins and not replace:
            raise DuplicateModelError(
                f"A CattyKit model named {plugin.name!r} is already registered."
            )

        self._plugins[plugin.name] = plugin

    def discover(self, *, force: bool = False) -> None:
        """Discover plugins registered through Python entry points."""
        if self._discovered and not force:
            return

        if force:
            self._plugins.clear()

        discovered = entry_points(group=ENTRY_POINT_GROUP)

        for entry_point in discovered:
            plugin = self._load_entry_point(entry_point)
            self.register(plugin)

        self._discovered = True

    def get(self, name: str) -> ModelPlugin:
        """Return a registered model plugin."""
        self.discover()

        try:
            return self._plugins[name]
        except KeyError as error:
            raise KeyError(
                f"No installed CattyKit model is registered as {name!r}."
            ) from error

    def contains(self, name: str) -> bool:
        """Return whether a model is registered."""
        self.discover()
        return name in self._plugins

    def names(self) -> tuple[str, ...]:
        """Return installed model names in sorted order."""
        self.discover()
        return tuple(sorted(self._plugins))

    def plugins(self) -> tuple[ModelPlugin, ...]:
        """Return installed plugins sorted by name."""
        self.discover()
        return tuple(self._plugins[name] for name in sorted(self._plugins))

    def register_many(
        self,
        plugins: Iterable[ModelPlugin],
        *,
        replace: bool = False,
    ) -> None:
        for plugin in plugins:
            self.register(plugin, replace=replace)

    @staticmethod
    def _load_entry_point(entry_point: EntryPoint) -> ModelPlugin:
        try:
            loaded_object = entry_point.load()
        except Exception as error:
            raise InvalidModelPluginError(
                f"Could not load model entry point "
                f"{entry_point.name!r} from {entry_point.value!r}."
            ) from error

        # Permit the entry point to expose either:
        #
        # 1. a ModelPlugin instance; or
        # 2. a zero-argument function returning a ModelPlugin.
        if isinstance(loaded_object, ModelPlugin):
            plugin = loaded_object
        elif callable(loaded_object):
            try:
                plugin = loaded_object()
            except Exception as error:
                raise InvalidModelPluginError(
                    f"Model entry point {entry_point.name!r} raised an "
                    "exception while creating its plugin descriptor."
                ) from error
        else:
            raise InvalidModelPluginError(
                f"Model entry point {entry_point.name!r} must expose a "
                "ModelPlugin or a callable returning one."
            )

        if not isinstance(plugin, ModelPlugin):
            raise InvalidModelPluginError(
                f"Model entry point {entry_point.name!r} returned "
                f"{type(plugin).__name__}, not ModelPlugin."
            )

        if plugin.name != entry_point.name:
            raise InvalidModelPluginError(
                f"Entry point name {entry_point.name!r} does not match "
                f"plugin name {plugin.name!r}."
            )

        return plugin

    @staticmethod
    def _validate_name(name: str) -> None:
        if not name:
            raise ValueError("A model name cannot be empty.")

        if not name.replace("-", "_").isalnum():
            raise ValueError(
                "Model names may contain letters, digits, underscores "
                f"and hyphens; got {name!r}."
            )


default_registry = ModelRegistry()
