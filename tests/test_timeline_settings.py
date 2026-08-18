"""
Fast, pytest-based tests for TimelineSettings (media/timeline_settings.py).
"""

from __future__ import annotations

import pytest

from videoforge.media.timeline_settings import (
    AudioLayout,
    ColorSpace,
    DurationMode,
    PixelFormat,
    TimelineSettings,
)


def test_defaults() -> None:
    settings = TimelineSettings()

    assert settings.width == 1920
    assert settings.height == 1080
    assert settings.fps == 30.0
    assert settings.color_space == ColorSpace.BT709
    assert settings.pixel_format == PixelFormat.YUV420P
    assert settings.duration_mode == DurationMode.AUTO
    assert settings.audio_layout == AudioLayout.STEREO


def test_computed_properties() -> None:
    settings = TimelineSettings()

    assert settings.resolution == "1920x1080"
    assert settings.aspect_ratio == pytest.approx(1.7778, abs=1e-3)
    assert settings.is_horizontal is True
    assert settings.is_vertical is False
    assert settings.frame_duration == pytest.approx(1.0 / 30.0)


def test_set_resolution() -> None:
    settings = TimelineSettings()
    settings.set_resolution(1280, 720)

    assert settings.resolution == "1280x720"


def test_set_fps() -> None:
    settings = TimelineSettings()
    settings.set_fps(60.0)
    assert settings.fps == 60.0


def test_set_fps_rejects_nonpositive() -> None:
    settings = TimelineSettings()

    with pytest.raises(ValueError, match="greater than zero"):
        settings.set_fps(0)


def test_set_audio() -> None:
    settings = TimelineSettings()
    settings.set_audio(44100, 6)

    assert settings.sample_rate == 44100
    assert settings.channels == 6


@pytest.mark.parametrize(
    "method,expected",
    [
        ("portrait", (1080, 1920)),
        ("landscape", (1920, 1080)),
        ("square", (1080, 1080)),
        ("cinema_4k", (4096, 2160)),
        ("uhd_4k", (3840, 2160)),
    ],
)
def test_resolution_presets(method: str, expected: tuple[int, int]) -> None:
    settings = TimelineSettings()
    getattr(settings, method)()

    assert (settings.width, settings.height) == expected


def test_portrait_is_vertical() -> None:
    settings = TimelineSettings()
    settings.portrait()

    assert settings.is_vertical is True
    assert settings.is_horizontal is False
