"""
Fast, pytest-based tests for Clipboard (editor/clipboard.py).
"""

from __future__ import annotations

from pathlib import Path

import pytest

from videoforge.editor.clipboard import Clipboard
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
def track(asset: MediaAsset) -> Track:
    t = Track(name="V1")
    t.add_clip(_clip(asset, 0, 10, 0))
    t.add_clip(_clip(asset, 0, 10, 20))
    return t


def test_copy_clip_stores_a_clone(track: Track) -> None:
    clip = track.clips[0]
    clipboard = Clipboard()

    clipboard.copy_clip(clip)

    assert clipboard.clip_count == 1
    assert clipboard.clips[0].id != clip.id
    assert clipboard.clips[0].timeline_start == clip.timeline_start


def test_copy_clips_preserves_relative_timing(track: Track) -> None:
    clipboard = Clipboard()
    clipboard.copy_clips(track.clips)

    assert clipboard.clip_count == 2
    assert clipboard._relative_positions == [0.0, 20.0]


def test_cut_clip_removes_from_track(track: Track) -> None:
    clip = track.clips[0]
    clipboard = Clipboard()

    clipboard.cut_clip(track, clip)

    assert clip not in track.clips
    assert clipboard.clip_count == 1


def test_duplicate_clip_adds_offset_copy(track: Track) -> None:
    clip = track.clips[0]  # 0..10
    clipboard = Clipboard()

    dup = clipboard.duplicate_clip(track, clip, offset=1.0)

    assert dup.id != clip.id
    assert dup.timeline_start == pytest.approx(11.0)  # clip.timeline_end + 1
    assert dup in track.clips


def test_paste_reconstructs_relative_positions(track: Track) -> None:
    clipboard = Clipboard()
    clipboard.copy_clips(track.clips)

    empty_track = Track(name="V2")
    pasted = clipboard.paste(empty_track, 100.0)

    assert len(pasted) == 2
    assert sorted(c.timeline_start for c in pasted) == [100.0, 120.0]


def test_copy_selected_only_copies_selected_clips(track: Track) -> None:
    track.clips[0].select()
    clipboard = Clipboard()

    timeline = Timeline()
    timeline.add_track(track)

    clipboard.copy_selected(timeline)

    assert clipboard.clip_count == 1
    assert clipboard.clips[0].timeline_start == track.clips[0].timeline_start


def test_cut_selected_removes_selected_clips_from_their_tracks(track: Track) -> None:
    """
    Regression test: cut_selected() previously used
    dict[Track, list[Clip]] as an internal accumulator, but Track (a
    Pydantic model) is not hashable - every call raised
    TypeError: unhashable type: 'Track'. Fixed by switching to a list
    of (track, clips) pairs.
    """
    track.clips[0].select()
    clipboard = Clipboard()

    timeline = Timeline()
    timeline.add_track(track)

    clipboard.cut_selected(timeline)  # previously always raised TypeError

    assert clipboard.clip_count == 1
    assert track.clip_count == 1
    assert track.clips[0].selected is False  # the remaining, unselected clip


def test_cut_selected_across_multiple_tracks(asset) -> None:
    track_a = Track(name="A")
    track_a.add_clip(_clip(asset, 0, 10, 0))
    track_a.clips[0].select()

    track_b = Track(name="B")
    track_b.add_clip(_clip(asset, 0, 10, 0))
    track_b.clips[0].select()

    timeline = Timeline()
    timeline.add_track(track_a)
    timeline.add_track(track_b)

    clipboard = Clipboard()
    clipboard.cut_selected(timeline)

    assert clipboard.clip_count == 2
    assert track_a.is_empty
    assert track_b.is_empty
