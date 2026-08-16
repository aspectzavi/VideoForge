"""
Plugin base class.

A Plugin is a self-contained, discoverable unit of functionality that
can be registered with PluginRegistry, loaded, executed, and unloaded
independently of VideoForge's core Operation/Pipeline system.

Plugins are intentionally a separate concept from Operations:
Operations build FFmpegJob objects for the Pipeline to execute;
Plugins are a general extension point (an AI provider, an export
destination, a social-media publishing integration, a custom effect)
that may or may not involve FFmpeg at all. A plugin is free to
delegate to Operations/Pipeline internally.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class Plugin(ABC):
    """
    Base class for every VideoForge plugin.

    Lifecycle

        register()  (PluginRegistry)
            -> load()
        execute()   (called any number of times while loaded)
        unregister() (PluginRegistry)
            -> unload()

    Subclasses must set `name` and implement `execute()`. `version`,
    `description`, and `category` are optional metadata.
    """

    name: str = ""
    version: str = "0.1.0"
    description: str = ""
    category: str = "general"

    def __init__(self) -> None:
        self._loaded = False

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def load(self) -> None:
        """
        Called once by PluginRegistry.register() before the plugin
        becomes available for execute(). Override for setup (opening
        connections, loading models, validating configuration, etc).

        Raising here aborts registration - the plugin is never added
        to the registry (see PluginRegistry.register()).
        """

        self._loaded = True

    # ------------------------------------------------------------------

    def unload(self) -> None:
        """
        Called once by PluginRegistry.unregister(). Override for
        cleanup (closing connections, releasing resources, etc).
        """

        self._loaded = False

    # ------------------------------------------------------------------

    @property
    def is_loaded(self) -> bool:
        return self._loaded

    # ------------------------------------------------------------------
    # Execution
    # ------------------------------------------------------------------

    @abstractmethod
    def execute(self, *args: Any, **kwargs: Any) -> Any:
        """
        Run the plugin's main functionality.

        Subclasses define their own argument signature; PluginRegistry
        passes through *args/**kwargs unchanged.
        """

        raise NotImplementedError

    # ------------------------------------------------------------------

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}("
            f"name={self.name!r}, "
            f"version={self.version!r}, "
            f"category={self.category!r}, "
            f"loaded={self._loaded})"
        )
