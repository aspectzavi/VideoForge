"""
Fast, pytest-based tests for TimelineUtils (editor/timeline_utils.py).
"""

from __future__ import annotations

from pathlib import Path

import pytest

from videoforge.editor.timeline_utils import TimelineUtils
from videoforge.media.asset import MediaAsset
from videoforge.media.clip import Clip
from videoforge.media.timeline import Timeline
from videoforge.media.track import Track

SAMPLE_MEDIA = Path("tests/sample_media/input.mp4")


@pytest.fixture
def asset() -> MediaAsset:
    return MediaAsset.load(SAMPLE_MEDIA)


def _clip(asset: MediaAsset, position: float, duration: float = 10.0) -> Clip:
    c = Clip(asset=asset)
    c.trim(0, duration)
    c.move(position)
    return c


@pytest.fixture
def track(asset: MediaAsset) -> Track:
    t = Track(name="V1")
    t.add_clip(_clip(asset, 20))  # deliberately out of order
    t.add_clip(_clip(asset, 0))
    return t


@pytest.fixture
def timeline(track: Track) -> Timeline:
    tl = Timeline()
    tl.add_track(track)
    return tl


def test_sort_track_orders_by_timeline_start(track: Track) -> None:
    TimelineUtils.sort_track(track)
    assert [c.timeline_start for c in track.clips] == [0.0, 20.0]


def test_sort_timeline_sorts_every_track(timeline: Timeline) -> None:
    TimelineUtils.sort_timeline(timeline)
    assert [c.timeline_start for c in timeline.tracks[0].clips] == [0.0, 20.0]


def test_find_clip_by_id(timeline: Timeline, track: Track) -> None:
    target = track.clips[0]

    found = TimelineUtils.find_clip(timeline, target.id)

    assert found is target
    assert TimelineUtils.find_clip(timeline, "missing") is None


def test_find_track_of_clip(timeline: Timeline, track: Track) -> None:
    clip = track.clips[0]

    assert TimelineUtils.find_track_of_clip(timeline, clip) is track


def test_find_track_of_clip_returns_none_for_stray_clip(
    timeline: Timeline, asset: MediaAsset
) -> None:
    stray = _clip(asset, 0)
    assert TimelineUtils.find_track_of_clip(timeline, stray) is None


def test_timeline_duration_matches_max_track_duration(timeline: Timeline) -> None:
    assert TimelineUtils.timeline_duration(timeline) == pytest.approx(30.0)


def test_timeline_duration_zero_when_no_tracks() -> None:
    empty = Timeline()
    assert TimelineUtils.timeline_duration(empty) == 0.0


def test_clips_overlap(asset: MediaAsset) -> None:
    a = _clip(asset, 0, 10)  # 0..10
    b = _clip(asset, 5, 10)  # 5..15
    c = _clip(asset, 20, 10)  # 20..30

    assert TimelineUtils.clips_overlap(a, b) is True
    assert TimelineUtils.clips_overlap(a, c) is False


def test_overlapping_clips_and_has_overlap(asset: MediaAsset) -> None:
    track = Track(name="V1")
    a = _clip(asset, 0, 10)
    b = _clip(asset, 5, 10)
    track.clips = [a, b]  # deliberately overlapping, bypassing add_clip

    assert TimelineUtils.overlapping_clips(track, a) == [b]
    assert TimelineUtils.has_overlap(track, a) is True


def test_gap_after_and_gap_before(asset: MediaAsset) -> None:
    track = Track(name="V1")
    a = _clip(asset, 0, 10)  # 0..10
    b = _clip(asset, 15, 10)  # 15..25, 5s gap after a
    track.add_clip(a)
    track.add_clip(b)

    assert TimelineUtils.gap_after(a, track) == pytest.approx(5.0)
    assert TimelineUtils.gap_before(b, track) == pytest.approx(5.0)
    assert TimelineUtils.gap_before(a, track) == pytest.approx(0.0)
    assert TimelineUtils.gap_after(b, track) == float("inf")


def test_ensure_clip_in_track_raises_for_missing_clip(
    track: Track, asset: MediaAsset
) -> None:
    stray = _clip(asset, 0)

    with pytest.raises(ValueError, match="not part of track"):
        TimelineUtils.ensure_clip_in_track(track, stray)


def test_ensure_positive_time_rejects_negative() -> None:
    with pytest.raises(ValueError, match="cannot be negative"):
        TimelineUtils.ensure_positive_time(-1.0)


def test_move_clip_validates_and_moves(asset: MediaAsset) -> None:
    clip = _clip(asset, 0)
    TimelineUtils.move_clip(clip, 50.0)
    assert clip.timeline_start == pytest.approx(50.0)

    with pytest.raises(ValueError):
        TimelineUtils.move_clip(clip, -1.0)


def test_offset_clip_clamps_at_zero(asset: MediaAsset) -> None:
    clip = _clip(asset, 5)
    TimelineUtils.offset_clip(clip, -1000.0)
    assert clip.timeline_start == pytest.approx(0.0)


def test_ripple_track_shifts_and_sorts(asset: MediaAsset) -> None:
    track = Track(name="V1")
    a = _clip(asset, 0, 10)
    b = _clip(asset, 20, 10)
    track.clips = [a, b]

    TimelineUtils.ripple_track(track, 20.0, 5.0)

    assert a.timeline_start == pytest.approx(0.0)
    assert b.timeline_start == pytest.approx(25.0)


def test_ripple_timeline_shifts_every_track(timeline: Timeline, track: Track) -> None:
    TimelineUtils.ripple_timeline(timeline, 15.0, 5.0)

    starts = sorted(c.timeline_start for c in track.clips)
    assert starts == [0.0, 25.0]
