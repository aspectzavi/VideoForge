"""
VideoForge plugin system.

Public API:

    from videoforge.plugins import Plugin, PluginRegistry, plugin_registry

Concrete plugins live in category subpackages (plugins.ai,
plugins.effects, plugins.export, plugins.social) - those subpackages
are currently empty namespaces waiting for real plugins.
"""

from __future__ import annotations

from videoforge.plugins.base import Plugin
from videoforge.plugins.registry import PluginRegistry, plugin_registry

__all__ = [
    "Plugin",
    "PluginRegistry",
    "plugin_registry",
]
