"""
Fast, pytest-based tests for Keyframe/KeyframeTrack (media/keyframe.py).

This module previously contained an unreferenced duplicate Project
class (see the module docstring in keyframe.py for the full story) -
these tests cover the real Keyframe/KeyframeTrack content it was
replaced with.
"""

from __future__ import annotations

import pytest

from videoforge.media.keyframe import InterpolationType, Keyframe, KeyframeTrack


def test_keyframe_defaults() -> None:
    kf = Keyframe(time=1.0, value=5.0)

    assert kf.interpolation == InterpolationType.LINEAR
    assert kf.id


def test_track_defaults() -> None:
    track = KeyframeTrack(name="opacity")

    assert track.is_empty is True
    assert track.keyframe_count == 0
    assert track.start_time is None
    assert track.end_time is None
    assert len(track) == 0


def test_add_keyframe_sorts_by_time() -> None:
    track = KeyframeTrack(name="opacity")

    track.add_keyframe(10.0, 1.0)
    track.add_keyframe(0.0, 0.0)
    track.add_keyframe(5.0, 0.5)

    assert [kf.time for kf in track.keyframes] == [0.0, 5.0, 10.0]
    assert track.start_time == 0.0
    assert track.end_time == 10.0


def test_add_keyframe_replaces_existing_at_same_time() -> None:
    track = KeyframeTrack(name="opacity")

    track.add_keyframe(5.0, 1.0)
    track.add_keyframe(5.0, 2.0)

    assert track.keyframe_count == 1
    assert track.keyframes[0].value == 2.0


def test_remove_keyframe() -> None:
    track = KeyframeTrack(name="opacity")
    kf = track.add_keyframe(0.0, 1.0)

    assert track.remove_keyframe(kf) is True
    assert track.remove_keyframe(kf) is False
    assert track.is_empty is True


def test_keyframe_at_uses_tolerance() -> None:
    track = KeyframeTrack(name="opacity")
    track.add_keyframe(5.0, 1.0)

    assert track.keyframe_at(5.0) is not None
    assert track.keyframe_at(5.0000001) is not None  # within default tolerance
    assert track.keyframe_at(5.1) is None


def test_clear() -> None:
    track = KeyframeTrack(name="opacity")
    track.add_keyframe(0.0, 1.0)
    track.clear()
    assert track.is_empty is True


def test_value_at_no_keyframes_returns_none() -> None:
    track = KeyframeTrack(name="opacity")
    assert track.value_at(5.0) is None


def test_value_at_clamps_outside_range() -> None:
    track = KeyframeTrack(name="opacity")
    track.add_keyframe(10.0, 1.0)
    track.add_keyframe(20.0, 2.0)

    assert track.value_at(0.0) == 1.0  # before range
    assert track.value_at(100.0) == 2.0  # after range


def test_value_at_linear_interpolation() -> None:
    track = KeyframeTrack(name="opacity")
    track.add_keyframe(0.0, 0.0)
    track.add_keyframe(10.0, 1.0)

    assert track.value_at(0.0) == pytest.approx(0.0)
    assert track.value_at(5.0) == pytest.approx(0.5)
    assert track.value_at(10.0) == pytest.approx(1.0)


def test_value_at_hold_interpolation() -> None:
    track = KeyframeTrack(name="opacity")
    track.add_keyframe(0.0, 0.0)
    track.add_keyframe(10.0, 1.0, interpolation=InterpolationType.HOLD)

    # HOLD on the right keyframe means the segment stays at the left
    # keyframe's value until snapping at the right keyframe itself.
    assert track.value_at(5.0) == pytest.approx(0.0)
    assert track.value_at(10.0) == pytest.approx(1.0)


@pytest.mark.parametrize(
    "interpolation",
    [
        InterpolationType.EASE_IN,
        InterpolationType.EASE_OUT,
        InterpolationType.EASE_IN_OUT,
    ],
)
def test_value_at_easing_stays_within_bounds(
    interpolation: InterpolationType,
) -> None:
    track = KeyframeTrack(name="opacity")
    track.add_keyframe(0.0, 0.0)
    track.add_keyframe(10.0, 1.0, interpolation=interpolation)

    for t in (1.0, 3.0, 5.0, 7.0, 9.0):
        value = track.value_at(t)
        assert 0.0 <= value <= 1.0

    # endpoints are always exact regardless of easing curve
    assert track.value_at(0.0) == pytest.approx(0.0)
    assert track.value_at(10.0) == pytest.approx(1.0)


def test_clone_gets_new_keyframe_ids_and_is_independent() -> None:
    track = KeyframeTrack(name="opacity")
    kf = track.add_keyframe(0.0, 1.0)

    clone = track.clone()

    assert clone.keyframes[0].id != kf.id
    assert clone.keyframes[0].value == kf.value

    clone.add_keyframe(5.0, 0.5)
    assert track.keyframe_count == 1
