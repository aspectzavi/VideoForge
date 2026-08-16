"""
Integration test for the ColorGradePlugin example, run against real
FFmpeg on a short trimmed clip.

Proves the plugin architecture actually works end-to-end - registry
-> plugin.execute() -> real Pipeline -> real FFmpeg -> real output
file - not just that the mocked unit tests in tests/test_plugins.py
look right in isolation.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from videoforge.ffmpeg.pipeline import Pipeline
from videoforge.operations.video.trim import TrimOperation
from videoforge.plugins.effects.color_grade import ColorGradePlugin
from videoforge.plugins.registry import PluginRegistry

SAMPLE_INPUT = Path("tests/sample_media/input.mp4")


@pytest.fixture(scope="module")
def short_clip() -> Path:
    result = Pipeline().add(TrimOperation(0.0, 2.0)).run(SAMPLE_INPUT)
    assert result.success
    return result.context.input_file


@pytest.mark.integration
def test_real_color_grade_plugin_via_registry(short_clip: Path) -> None:
    registry = PluginRegistry()
    registry.register(ColorGradePlugin())

    output = registry.execute(
        "color_grade",
        short_clip,
        brightness=0.05,
        contrast=1.1,
        saturation=1.2,
    )

    assert output.exists()
    assert output.stat().st_size > 0

    registry.unregister("color_grade")
    assert "color_grade" not in registry
