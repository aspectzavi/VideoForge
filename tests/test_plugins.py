"""
Fast, pytest-based tests for the plugin system (Plugin, PluginRegistry).

Uses small dummy Plugin subclasses throughout - no FFmpeg involved.
See tests/integration/test_plugins_integration.py for a real-FFmpeg
test of the ColorGradePlugin example.
"""

from __future__ import annotations

import pytest

from videoforge.engine.events import PluginLoadedEvent, PluginUnloadedEvent
from videoforge.engine.exceptions import PluginError, PluginExecutionError, PluginLoadError
from videoforge.plugins.base import Plugin
from videoforge.plugins.registry import PluginRegistry


class DummyPlugin(Plugin):
    name = "dummy"
    category = "test"

    def __init__(self) -> None:
        super().__init__()
        self.executed_with: tuple | None = None

    def execute(self, *args, **kwargs):
        self.executed_with = (args, kwargs)
        return "dummy-result"


class FailingLoadPlugin(Plugin):
    name = "failing_load"

    def load(self) -> None:
        raise RuntimeError("boom during load")

    def execute(self, *args, **kwargs):
        return None


class FailingUnloadPlugin(Plugin):
    name = "failing_unload"

    def unload(self) -> None:
        raise RuntimeError("boom during unload")

    def execute(self, *args, **kwargs):
        return None


class FailingExecutePlugin(Plugin):
    name = "failing_execute"

    def execute(self, *args, **kwargs):
        raise ValueError("boom during execute")


class NamelessPlugin(Plugin):
    name = ""

    def execute(self, *args, **kwargs):
        return None


@pytest.fixture
def registry() -> PluginRegistry:
    return PluginRegistry()


# ---------------------------------------------------------------------
# Base Plugin
# ---------------------------------------------------------------------


def test_plugin_starts_unloaded() -> None:
    plugin = DummyPlugin()
    assert plugin.is_loaded is False


def test_plugin_load_sets_loaded_flag() -> None:
    plugin = DummyPlugin()
    plugin.load()
    assert plugin.is_loaded is True


def test_plugin_unload_clears_loaded_flag() -> None:
    plugin = DummyPlugin()
    plugin.load()
    plugin.unload()
    assert plugin.is_loaded is False


def test_plugin_is_abstract_without_execute() -> None:
    with pytest.raises(TypeError):
        Plugin()  # type: ignore[abstract]


# ---------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------


def test_register_loads_and_adds_plugin(registry: PluginRegistry) -> None:
    plugin = DummyPlugin()
    registry.register(plugin)

    assert plugin.is_loaded is True
    assert "dummy" in registry
    assert registry.get("dummy") is plugin
    assert len(registry) == 1


def test_register_rejects_nameless_plugin(registry: PluginRegistry) -> None:
    with pytest.raises(PluginLoadError, match="non-empty name"):
        registry.register(NamelessPlugin())

    assert len(registry) == 0


def test_register_rejects_duplicate_name(registry: PluginRegistry) -> None:
    registry.register(DummyPlugin())

    with pytest.raises(PluginLoadError, match="already registered"):
        registry.register(DummyPlugin())


def test_register_replace_true_overwrites(registry: PluginRegistry) -> None:
    first = DummyPlugin()
    second = DummyPlugin()

    registry.register(first)
    registry.register(second, replace=True)

    assert registry.get("dummy") is second


def test_register_failed_load_does_not_add_plugin(registry: PluginRegistry) -> None:
    with pytest.raises(PluginLoadError, match="failed to load"):
        registry.register(FailingLoadPlugin())

    # fails safely - never half-registered
    assert "failing_load" not in registry
    assert len(registry) == 0


def test_register_emits_plugin_loaded_event(registry: PluginRegistry) -> None:
    from videoforge.engine.dispatcher import dispatcher

    received: list[PluginLoadedEvent] = []
    handler = dispatcher.subscribe(PluginLoadedEvent, received.append)

    try:
        registry.register(DummyPlugin())
    finally:
        dispatcher.unsubscribe(PluginLoadedEvent, handler)

    assert len(received) == 1
    assert received[0].plugin == "dummy"


# ---------------------------------------------------------------------
# Unregistration
# ---------------------------------------------------------------------


def test_unregister_unloads_and_removes(registry: PluginRegistry) -> None:
    plugin = DummyPlugin()
    registry.register(plugin)

    registry.unregister("dummy")

    assert plugin.is_loaded is False
    assert "dummy" not in registry
    assert len(registry) == 0


def test_unregister_missing_plugin_raises(registry: PluginRegistry) -> None:
    with pytest.raises(PluginError, match="not registered"):
        registry.unregister("does-not-exist")


def test_unregister_removes_even_if_unload_fails(registry: PluginRegistry) -> None:
    registry.register(FailingUnloadPlugin())

    with pytest.raises(PluginError, match="failed to unload cleanly"):
        registry.unregister("failing_unload")

    # still removed - a failing unload() never leaves it stuck
    assert "failing_unload" not in registry


def test_unregister_emits_plugin_unloaded_event(registry: PluginRegistry) -> None:
    from videoforge.engine.dispatcher import dispatcher

    registry.register(DummyPlugin())

    received: list[PluginUnloadedEvent] = []
    handler = dispatcher.subscribe(PluginUnloadedEvent, received.append)

    try:
        registry.unregister("dummy")
    finally:
        dispatcher.unsubscribe(PluginUnloadedEvent, handler)

    assert len(received) == 1
    assert received[0].plugin == "dummy"


# ---------------------------------------------------------------------
# Lookup
# ---------------------------------------------------------------------


def test_get_returns_none_for_unknown_plugin(registry: PluginRegistry) -> None:
    assert registry.get("does-not-exist") is None


def test_list_plugins_filters_by_category(registry: PluginRegistry) -> None:
    class EffectPlugin(Plugin):
        name = "effect_one"
        category = "effects"

        def execute(self, *a, **kw):
            return None

    class ExportPlugin(Plugin):
        name = "export_one"
        category = "export"

        def execute(self, *a, **kw):
            return None

    registry.register(EffectPlugin())
    registry.register(ExportPlugin())

    assert len(registry.list_plugins()) == 2
    effects = registry.list_plugins(category="effects")
    assert [p.name for p in effects] == ["effect_one"]


# ---------------------------------------------------------------------
# Execution
# ---------------------------------------------------------------------


def test_execute_calls_plugin_and_returns_result(registry: PluginRegistry) -> None:
    plugin = DummyPlugin()
    registry.register(plugin)

    result = registry.execute("dummy", 1, 2, key="value")

    assert result == "dummy-result"
    assert plugin.executed_with == ((1, 2), {"key": "value"})


def test_execute_missing_plugin_raises(registry: PluginRegistry) -> None:
    with pytest.raises(PluginError, match="not registered"):
        registry.execute("does-not-exist")


def test_execute_wraps_plugin_exceptions(registry: PluginRegistry) -> None:
    registry.register(FailingExecutePlugin())

    with pytest.raises(PluginExecutionError, match="execution failed"):
        registry.execute("failing_execute")


# ---------------------------------------------------------------------
# Bulk operations
# ---------------------------------------------------------------------


def test_clear_unregisters_everything(registry: PluginRegistry) -> None:
    registry.register(DummyPlugin())

    class Other(Plugin):
        name = "other"

        def execute(self, *a, **kw):
            return None

    registry.register(Other())

    registry.clear()

    assert len(registry) == 0
