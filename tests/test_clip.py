"""
Fast, pytest-based tests for Clip.

MediaAsset.load() alone doesn't probe (see test_asset.py), so these
tests avoid triggering real ffprobe by always giving clips an explicit
source_end via trim() rather than relying on asset.duration.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from videoforge.media.asset import MediaAsset
from videoforge.media.clip import Clip
from videoforge.media.effect import Effect

SAMPLE_MEDIA = Path("tests/sample_media/input.mp4")


@pytest.fixture
def asset() -> MediaAsset:
    return MediaAsset.load(SAMPLE_MEDIA)


@pytest.fixture
def clip(asset: MediaAsset) -> Clip:
    c = Clip(asset=asset)
    c.trim(10, 30)
    c.move(5)
    return c


# ---------------------------------------------------------------------
# Computed properties
# ---------------------------------------------------------------------


def test_clip_computed_durations(clip: Clip) -> None:
    assert clip.source_duration == pytest.approx(20.0)
    assert clip.duration == pytest.approx(20.0)
    assert clip.timeline_start == pytest.approx(5.0)
    assert clip.timeline_end == pytest.approx(25.0)


def test_clip_duration_reflects_speed(asset: MediaAsset) -> None:
    c = Clip(asset=asset)
    c.trim(0, 20)
    c.set_speed(2.0)

    assert c.source_duration == pytest.approx(20.0)
    assert c.duration == pytest.approx(10.0)
    assert c.timeline_end == pytest.approx(10.0)


def test_clip_duration_is_zero_for_nonpositive_speed(asset: MediaAsset) -> None:
    c = Clip(asset=asset)
    c.trim(0, 20)

    # set_speed() itself rejects <= 0, but duration must still be
    # well-defined (not raise/divide-by-zero) if speed is ever 0.
    c.speed = 0.0

    assert c.duration == 0.0


# ---------------------------------------------------------------------
# trim / move / offset / resize / set_speed
# ---------------------------------------------------------------------


def test_clip_trim_sets_source_range(asset: MediaAsset) -> None:
    c = Clip(asset=asset)
    c.trim(2, 8)

    assert c.source_start == pytest.approx(2.0)
    assert c.source_end == pytest.approx(8.0)


def test_clip_trim_rejects_end_before_start(asset: MediaAsset) -> None:
    c = Clip(asset=asset)

    with pytest.raises(ValueError):
        c.trim(10, 5)


def test_clip_move_sets_absolute_position(clip: Clip) -> None:
    clip.move(100)
    assert clip.timeline_start == pytest.approx(100.0)


def test_clip_move_clamps_at_zero(clip: Clip) -> None:
    clip.move(-50)
    assert clip.timeline_start == pytest.approx(0.0)


def test_clip_offset_is_relative_and_clamps_at_zero(clip: Clip) -> None:
    clip.offset(10)
    assert clip.timeline_start == pytest.approx(15.0)

    clip.offset(-1000)
    assert clip.timeline_start == pytest.approx(0.0)


def test_clip_resize_extends_source_end(asset: MediaAsset) -> None:
    c = Clip(asset=asset)
    c.trim(5, 15)
    c.set_speed(2.0)

    c.resize(3.0)  # 3s of timeline duration at 2x speed = 6s of source

    assert c.source_end == pytest.approx(11.0)  # source_start(5) + 6


def test_clip_resize_rejects_nonpositive_duration(clip: Clip) -> None:
    with pytest.raises(ValueError):
        clip.resize(0)

    with pytest.raises(ValueError):
        clip.resize(-1)


def test_clip_set_speed_rejects_nonpositive(clip: Clip) -> None:
    with pytest.raises(ValueError):
        clip.set_speed(0)

    with pytest.raises(ValueError):
        clip.set_speed(-2)


# ---------------------------------------------------------------------
# State toggles
# ---------------------------------------------------------------------


def test_clip_mute_unmute(clip: Clip) -> None:
    assert clip.muted is False
    clip.mute()
    assert clip.muted is True
    clip.unmute()
    assert clip.muted is False


def test_clip_enable_disable_and_is_enabled(clip: Clip) -> None:
    assert clip.is_enabled is True

    clip.disable()
    assert clip.enabled is False
    assert clip.is_enabled is False

    clip.enable()
    assert clip.is_enabled is True

    # is_enabled also requires not-locked.
    clip.lock()
    assert clip.is_enabled is False
    clip.unlock()
    assert clip.is_enabled is True


def test_clip_select_deselect(clip: Clip) -> None:
    assert clip.selected is False
    clip.select()
    assert clip.selected is True
    clip.deselect()
    assert clip.selected is False


def test_clip_set_volume_is_clamped_0_to_2(clip: Clip) -> None:
    clip.set_volume(1.5)
    assert clip.volume == pytest.approx(1.5)

    clip.set_volume(5.0)
    assert clip.volume == pytest.approx(2.0)

    clip.set_volume(-1.0)
    assert clip.volume == pytest.approx(0.0)


# ---------------------------------------------------------------------
# Effects
# ---------------------------------------------------------------------


def test_clip_effect_management(clip: Clip) -> None:
    assert clip.has_effects is False

    effect = Effect(name="Test Effect")
    clip.add_effect(effect)

    assert clip.has_effects is True
    assert effect in clip.effects

    clip.remove_effect(effect)
    assert clip.has_effects is False

    clip.add_effect(Effect(name="A"))
    clip.add_effect(Effect(name="B"))
    clip.clear_effects()
    assert clip.effects == []


# ---------------------------------------------------------------------
# duplicate / clone / split
# ---------------------------------------------------------------------


def test_clip_duplicate_offsets_and_gets_new_id(clip: Clip) -> None:
    original_start = clip.timeline_start

    dup = clip.duplicate(offset=2.0)

    assert dup.id != clip.id
    assert dup.timeline_start == pytest.approx(original_start + 2.0)


def test_clip_clone_is_independent(clip: Clip) -> None:
    clone = clip.clone()

    assert clone.id != clip.id
    assert clone.timeline_start == clip.timeline_start

    clone.move(500)

    assert clip.timeline_start != 500


def test_clip_split_produces_two_clips_at_correct_ranges(clip: Clip) -> None:
    # clip: timeline_start=5, timeline_end=25, source 10..30, speed=1
    left, right = clip.split(15.0)

    assert left.timeline_start == pytest.approx(5.0)
    assert left.timeline_end == pytest.approx(15.0)
    assert left.source_start == pytest.approx(10.0)
    assert left.source_end == pytest.approx(20.0)

    assert right.timeline_start == pytest.approx(15.0)
    assert right.timeline_end == pytest.approx(25.0)
    assert right.source_start == pytest.approx(20.0)
    assert right.source_end == pytest.approx(30.0)

    assert left.id != clip.id
    assert right.id != clip.id
    assert left.id != right.id


def test_clip_split_clears_transitions_across_the_cut(clip: Clip) -> None:
    from videoforge.media.transition import Transition, TransitionType

    clip.transition_in = Transition(type=TransitionType.FADE)
    clip.transition_out = Transition(type=TransitionType.FADE)

    left, right = clip.split(15.0)

    # transition_in on the original start is preserved on the left half
    assert left.transition_in is not None
    assert left.transition_out is None

    # transition_out on the original end is preserved on the right half
    assert right.transition_out is not None
    assert right.transition_in is None


def test_clip_split_rejects_position_outside_clip(clip: Clip) -> None:
    with pytest.raises(ValueError):
        clip.split(4.0)  # before timeline_start

    with pytest.raises(ValueError):
        clip.split(25.0)  # at/after timeline_end

    with pytest.raises(ValueError):
        clip.split(30.0)  # well past the clip
