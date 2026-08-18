"""
Fast, pytest-based tests for TimelineValidator (editor/validator.py).
"""

from __future__ import annotations

from pathlib import Path

import pytest

from videoforge.editor.validator import TimelineValidator
from videoforge.media.asset import MediaAsset
from videoforge.media.clip import Clip
from videoforge.media.timeline import Timeline
from videoforge.media.track import Track

SAMPLE_MEDIA = Path("tests/sample_media/input.mp4")


@pytest.fixture
def asset() -> MediaAsset:
    return MediaAsset.load(SAMPLE_MEDIA)


def _clip(asset: MediaAsset, start: float, end: float, position: float) -> Clip:
    c = Clip(asset=asset)
    c.trim(start, end)
    c.move(position)
    return c


@pytest.fixture
def validator() -> TimelineValidator:
    return TimelineValidator()


def test_ensure_raises_with_message(validator: TimelineValidator) -> None:
    with pytest.raises(ValueError, match="boom"):
        validator.ensure(False, "boom")

    validator.ensure(True, "unreachable")  # should not raise


def test_validate_full_timeline_passes_for_clean_state(
    validator: TimelineValidator, asset: MediaAsset
) -> None:
    track = Track(name="V1")
    track.add_clip(_clip(asset, 0, 10, 0))
    timeline = Timeline()
    timeline.add_track(track)

    assert validator.validate(timeline) is True


def test_validate_none_timeline_raises(validator: TimelineValidator) -> None:
    with pytest.raises(ValueError, match="Timeline cannot be None"):
        validator.validate_timeline(None)


def test_validate_time_rejects_negative(validator: TimelineValidator) -> None:
    with pytest.raises(ValueError, match="cannot be negative"):
        validator.validate_time(-1.0)

    validator.validate_time(0.0)  # should not raise


def test_validate_duration_rejects_nonpositive(validator: TimelineValidator) -> None:
    with pytest.raises(ValueError, match="greater than zero"):
        validator.validate_duration(0.0)


def test_validate_clip_in_track(
    validator: TimelineValidator, asset: MediaAsset
) -> None:
    track = Track(name="V1")
    clip = _clip(asset, 0, 10, 0)
    track.add_clip(clip)

    validator.validate_clip_in_track(clip, track)  # should not raise

    stray = _clip(asset, 0, 5, 0)
    with pytest.raises(ValueError, match="not contained in track"):
        validator.validate_clip_in_track(stray, track)


def test_validate_track_index(
    validator: TimelineValidator, asset: MediaAsset
) -> None:
    timeline = Timeline()
    timeline.add_track(Track(name="V1"))

    validator.validate_track_index(timeline, 0)  # should not raise

    with pytest.raises(ValueError, match="out of range"):
        validator.validate_track_index(timeline, 5)


def test_validate_track_unlocked(validator: TimelineValidator) -> None:
    track = Track(name="V1")
    validator.validate_track_unlocked(track)

    track.lock()
    with pytest.raises(ValueError, match="Track is locked"):
        validator.validate_track_unlocked(track)


def test_validate_clip_unlocked(
    validator: TimelineValidator, asset: MediaAsset
) -> None:
    clip = _clip(asset, 0, 10, 0)
    validator.validate_clip_unlocked(clip)

    clip.lock()
    with pytest.raises(ValueError, match="Clip is locked"):
        validator.validate_clip_unlocked(clip)


def test_validate_no_overlap_detects_overlap(
    validator: TimelineValidator, asset: MediaAsset
) -> None:
    track = Track(name="V1")
    a = _clip(asset, 0, 10, 0)  # 0..10
    b = _clip(asset, 0, 10, 5)  # 5..15, overlaps a
    track.clips = [a, b]

    with pytest.raises(ValueError, match="overlaps"):
        validator.validate_no_overlap(track, a)


def test_validate_source_range(
    validator: TimelineValidator, asset: MediaAsset
) -> None:
    clip = _clip(asset, 5, 15, 0)
    validator.validate_source_range(clip)  # should not raise

    clip.source_start = -1.0
    with pytest.raises(ValueError, match="cannot be negative"):
        validator.validate_source_range(clip)


def test_validate_speed_opacity_volume(validator: TimelineValidator) -> None:
    validator.validate_speed(1.0)
    with pytest.raises(ValueError, match="greater than zero"):
        validator.validate_speed(0.0)

    validator.validate_opacity(0.5)
    with pytest.raises(ValueError, match="between 0 and 1"):
        validator.validate_opacity(1.5)

    validator.validate_volume(0.0)
    with pytest.raises(ValueError, match="cannot be negative"):
        validator.validate_volume(-0.1)
