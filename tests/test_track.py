"""
Fast, pytest-based tests for Track.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from videoforge.media.asset import MediaAsset
from videoforge.media.clip import Clip
from videoforge.media.effect import Effect
from videoforge.media.track import Track, TrackType

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
def track(asset: MediaAsset) -> Track:
    t = Track(name="Video Track 1")
    t.add_clip(_clip(asset, 0, 10, 0))
    t.add_clip(_clip(asset, 10, 20, 12))
    return t


# ---------------------------------------------------------------------
# Computed properties
# ---------------------------------------------------------------------


def test_track_computed_properties(track: Track) -> None:
    assert track.clip_count == 2
    assert track.is_empty is False
    assert track.duration == pytest.approx(22.0)  # second clip ends at 12+10
    assert track.start == pytest.approx(0.0)
    assert track.end == pytest.approx(22.0)


def test_track_is_empty_when_no_clips() -> None:
    t = Track()
    assert t.is_empty is True
    assert t.clip_count == 0
    assert t.duration == pytest.approx(0.0)


def test_track_enabled_locked_selected_clip_lists(track: Track) -> None:
    track.clips[0].disable()
    track.clips[1].lock()
    track.clips[1].select()

    assert track.enabled_clips == [track.clips[1]]
    assert track.locked_clips == 1
    assert track.selected_clips == [track.clips[1]]


# ---------------------------------------------------------------------
# add / insert / remove / ordering
# ---------------------------------------------------------------------


def test_track_add_clip_keeps_clips_sorted_by_start(asset: MediaAsset) -> None:
    t = Track()
    late = _clip(asset, 0, 5, 20)
    early = _clip(asset, 0, 5, 0)

    t.add_clip(late)
    t.add_clip(early)

    assert [c.timeline_start for c in t.clips] == [0.0, 20.0]


def test_track_insert_clip_moves_then_adds(asset: MediaAsset) -> None:
    t = Track()
    c = _clip(asset, 0, 5, 999)

    t.insert_clip(c, position=7.0)

    assert c.timeline_start == pytest.approx(7.0)
    assert t.clips == [c]


def test_track_remove_clip(track: Track) -> None:
    victim = track.clips[0]
    track.remove_clip(victim)

    assert track.clip_count == 1
    assert victim not in track.clips


def test_track_remove_clip_by_id(track: Track) -> None:
    victim_id = track.clips[0].id

    removed = track.remove_clip_by_id(victim_id)
    missing = track.remove_clip_by_id("does-not-exist")

    assert removed is True
    assert missing is False
    assert track.clip_count == 1


def test_track_clear(track: Track) -> None:
    track.clear()
    assert track.clip_count == 0
    assert track.is_empty is True


# ---------------------------------------------------------------------
# Queries
# ---------------------------------------------------------------------


def test_track_get_clip(track: Track) -> None:
    target = track.clips[0]

    assert track.get_clip(target.id) is target
    assert track.get_clip("does-not-exist") is None


def test_track_clip_at_returns_containing_clip_or_none(track: Track) -> None:
    first, second = track.clips

    assert track.clip_at(5.0) is first
    assert track.clip_at(15.0) is second
    assert track.clip_at(11.0) is None  # gap between clips (10..12)
    assert track.clip_at(999.0) is None


def test_track_first_and_last(track: Track) -> None:
    assert track.first() is track.clips[0]
    assert track.last() is track.clips[-1]


def test_track_first_and_last_are_none_when_empty() -> None:
    t = Track()
    assert t.first() is None
    assert t.last() is None


# ---------------------------------------------------------------------
# Overlap detection
# ---------------------------------------------------------------------


def test_track_overlaps_and_has_overlap(asset: MediaAsset, track: Track) -> None:
    # overlaps() returns the list of clips that overlap the candidate;
    # has_overlap() is just bool(overlaps()) for the same candidate.
    # track clips are at 0..10 and 12..22 — this candidate (5..11)
    # overlaps only the first (11 < 12, so the second is untouched).
    overlapping = _clip(asset, 0, 6, 5)
    non_overlapping = _clip(asset, 0, 1, 50)

    assert track.overlaps(overlapping) == [track.clips[0]]
    assert track.overlaps(non_overlapping) == []

    assert track.has_overlap(non_overlapping) is False
    assert track.has_overlap(overlapping) is True


def test_track_overlaps_excludes_the_clip_itself(track: Track) -> None:
    # A clip already in the track shouldn't be reported as overlapping
    # against its own position.
    assert track.overlaps(track.clips[0]) == []


# ---------------------------------------------------------------------
# Ripple editing
# ---------------------------------------------------------------------


def test_track_ripple_shifts_clips_at_or_after_start_time(track: Track) -> None:
    first, second = track.clips
    original_first_start = first.timeline_start

    track.ripple(start_time=6.0, delta=3.0)

    # first clip starts at 0, before start_time=6 -> untouched
    assert first.timeline_start == pytest.approx(original_first_start)
    # second clip starts at 12, at/after start_time -> shifted
    assert second.timeline_start == pytest.approx(15.0)


def test_track_ripple_negative_delta_clamps_at_zero(track: Track) -> None:
    track.ripple(start_time=0.0, delta=-1000.0)

    for c in track.clips:
        assert c.timeline_start == pytest.approx(0.0)


# ---------------------------------------------------------------------
# move_clip
# ---------------------------------------------------------------------


def test_track_move_clip_repositions_and_resorts(track: Track) -> None:
    first, second = track.clips

    # move_clip() takes the Clip object itself, not its id (unlike
    # remove_clip_by_id/get_clip, which take an id). Move `first`
    # (originally at 0) past `second` (at 12) to confirm the list
    # actually re-sorts rather than just mutating in place.
    track.move_clip(first, 20.0)

    assert track.clips == [second, first]
    assert first.timeline_start == pytest.approx(20.0)


# ---------------------------------------------------------------------
# State toggles
# ---------------------------------------------------------------------


def test_track_mute_unmute(track: Track) -> None:
    assert track.muted is False
    track.mute()
    assert track.muted is True
    track.unmute()
    assert track.muted is False


def test_track_lock_unlock(track: Track) -> None:
    assert track.locked is False
    track.lock()
    assert track.locked is True
    track.unlock()
    assert track.locked is False


def test_track_enable_disable(track: Track) -> None:
    assert track.enabled is True
    track.disable()
    assert track.enabled is False
    track.enable()
    assert track.enabled is True


def test_track_show_hide(track: Track) -> None:
    assert track.visible is True
    track.hide()
    assert track.visible is False
    track.show()
    assert track.visible is True


# ---------------------------------------------------------------------
# Effects
# ---------------------------------------------------------------------


def test_track_effect_management(track: Track) -> None:
    effect = Effect(name="Track Effect")
    track.add_effect(effect)

    assert effect in track.effects

    track.remove_effect(effect)
    assert effect not in track.effects

    track.add_effect(Effect(name="A"))
    track.add_effect(Effect(name="B"))
    track.clear_effects()
    assert track.effects == []


# ---------------------------------------------------------------------
# Iteration / clone / type
# ---------------------------------------------------------------------


def test_track_iter_clips_matches_clips_order(track: Track) -> None:
    assert list(track.iter_clips()) == track.clips


def test_track_clone_gets_new_id_and_is_independent(track: Track) -> None:
    clone = track.clone()

    assert clone.id != track.id
    assert clone.clip_count == track.clip_count

    clone.mute()

    assert track.muted is False


def test_track_type_default_and_explicit() -> None:
    default_track = Track()
    video_track = Track(type=TrackType.VIDEO)
    audio_track = Track(type=TrackType.AUDIO)

    assert default_track.type == TrackType.VIDEO
    assert video_track.type == TrackType.VIDEO
    assert audio_track.type == TrackType.AUDIO
