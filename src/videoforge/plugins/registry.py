"""
Plugin registry.

Tracks registered plugins, drives their load()/unload() lifecycle,
dispatches PluginLoadedEvent/PluginUnloadedEvent, and wraps execution
failures in PluginExecutionError so callers get a consistent error
type regardless of what a given plugin does internally.
"""

from __future__ import annotations

from typing import Any

from videoforge.engine.dispatcher import dispatcher
from videoforge.engine.events import PluginLoadedEvent, PluginUnloadedEvent
from videoforge.engine.exceptions import (
    PluginError,
    PluginExecutionError,
    PluginLoadError,
)
from videoforge.plugins.base import Plugin


class PluginRegistry:
    """
    Registers, loads, executes, and unloads Plugin instances.

    A single process-wide instance is exposed as
    `videoforge.plugins.registry.plugin_registry`, but nothing
    requires using that singleton - tests and isolated workflows can
    construct their own PluginRegistry().
    """

    def __init__(self) -> None:
        self._plugins: dict[str, Plugin] = {}

    # ------------------------------------------------------------------
    # Register / unregister
    # ------------------------------------------------------------------

    def register(
        self,
        plugin: Plugin,
        *,
        replace: bool = False,
    ) -> None:
        """
        Register and load a plugin.

        Raises PluginLoadError (without adding the plugin to the
        registry) if the name is invalid, already taken (unless
        replace=True), or if plugin.load() raises - a failed load
        never leaves a half-registered plugin behind.
        """

        if not plugin.name:
            raise PluginLoadError("Plugin must have a non-empty name.")

        if plugin.name in self._plugins and not replace:
            raise PluginLoadError(
                f"Plugin '{plugin.name}' is already registered "
                "(pass replace=True to replace it)."
            )

        try:
            plugin.load()
        except Exception as exc:
            raise PluginLoadError(
                f"Plugin '{plugin.name}' failed to load: {exc}"
            ) from exc

        self._plugins[plugin.name] = plugin

        dispatcher.emit(PluginLoadedEvent(plugin=plugin.name))

    # ------------------------------------------------------------------

    def unregister(
        self,
        name: str,
    ) -> None:
        """
        Unload and remove a plugin.

        The plugin is removed from the registry before unload() runs,
        so a failing unload() cannot leave a broken plugin stuck in
        the registry - the failure is reported as PluginError, but the
        plugin is gone either way. PluginUnloadedEvent fires in both
        cases, since it reflects registry state, not unload() success.
        """

        if name not in self._plugins:
            raise PluginError(f"Plugin '{name}' is not registered.")

        plugin = self._plugins.pop(name)

        try:
            plugin.unload()
        except Exception as exc:
            dispatcher.emit(PluginUnloadedEvent(plugin=name))
            raise PluginError(
                f"Plugin '{name}' failed to unload cleanly: {exc}"
            ) from exc

        dispatcher.emit(PluginUnloadedEvent(plugin=name))

    # ------------------------------------------------------------------
    # Lookup
    # ------------------------------------------------------------------

    def get(
        self,
        name: str,
    ) -> Plugin | None:
        return self._plugins.get(name)

    # ------------------------------------------------------------------

    def __contains__(
        self,
        name: str,
    ) -> bool:
        return name in self._plugins

    # ------------------------------------------------------------------

    def __len__(self) -> int:
        return len(self._plugins)

    # ------------------------------------------------------------------

    def list_plugins(
        self,
        *,
        category: str | None = None,
    ) -> list[Plugin]:
        plugins = list(self._plugins.values())

        if category is not None:
            plugins = [p for p in plugins if p.category == category]

        return plugins

    # ------------------------------------------------------------------
    # Execution
    # ------------------------------------------------------------------

    def execute(
        self,
        name: str,
        *args: Any,
        **kwargs: Any,
    ) -> Any:
        """
        Run a registered plugin's execute().

        Any exception raised by the plugin is wrapped in
        PluginExecutionError so callers can handle plugin failures
        uniformly, regardless of what each plugin does internally.
        """

        plugin = self._plugins.get(name)

        if plugin is None:
            raise PluginError(f"Plugin '{name}' is not registered.")

        try:
            return plugin.execute(*args, **kwargs)
        except Exception as exc:
            raise PluginExecutionError(
                f"Plugin '{name}' execution failed: {exc}"
            ) from exc

    # ------------------------------------------------------------------
    # Bulk operations
    # ------------------------------------------------------------------

    def clear(self) -> None:
        """Unregister every plugin."""

        for name in list(self._plugins):
            self.unregister(name)


# Process-wide default registry.
plugin_registry = PluginRegistry()
