"""
Fast, pytest-based tests for Composition (media/composition.py).
"""

from __future__ import annotations

from pathlib import Path

import pytest

from videoforge.media.clip import Clip
from videoforge.media.composition import Composition
from videoforge.media.asset import MediaAsset
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


def test_defaults() -> None:
    comp = Composition()

    assert comp.name == "Composition"
    assert comp.width == 1920
    assert comp.height == 1080
    assert comp.resolution == "1920x1080"
    assert comp.is_vertical is False
    assert comp.track_count == 0
    assert comp.clip_count == 0
    assert comp.duration == 0.0


def test_add_and_remove_track() -> None:
    comp = Composition()
    track = Track(name="V1")

    comp.add_track(track)
    assert comp.track_count == 1

    comp.remove_track(track)
    assert comp.track_count == 0


def test_add_clip_to_track_by_index(asset: MediaAsset) -> None:
    comp = Composition()
    comp.add_track(Track(name="V1"))
    clip = _clip(asset, 0)

    comp.add_clip(clip, track_index=0)

    assert comp.clip_count == 1
    assert comp.tracks[0].clips[0] is clip


def test_add_clip_raises_for_invalid_track_index(asset: MediaAsset) -> None:
    comp = Composition()
    clip = _clip(asset, 0)

    with pytest.raises(IndexError, match="Track index out of range"):
        comp.add_clip(clip, track_index=0)


def test_remove_clip_finds_it_across_tracks(asset: MediaAsset) -> None:
    comp = Composition()
    comp.add_track(Track(name="V1"))
    clip = _clip(asset, 0)
    comp.add_clip(clip)

    comp.remove_clip(clip)

    assert comp.clip_count == 0


def test_clips_at_respects_enabled_state(asset: MediaAsset) -> None:
    comp = Composition()
    track = Track(name="V1")
    clip = _clip(asset, 0, 10)
    track.add_clip(clip)
    comp.add_track(track)

    assert comp.clips_at(5.0) == [clip]

    clip.disable()
    assert comp.clips_at(5.0) == []


def test_clips_at_skips_disabled_tracks(asset: MediaAsset) -> None:
    comp = Composition()
    track = Track(name="V1")
    track.add_clip(_clip(asset, 0, 10))
    track.disable()
    comp.add_track(track)

    assert comp.clips_at(5.0) == []


def test_flatten_track_index_quirk(asset: MediaAsset) -> None:
    """
    Documents a real quirk rather than an idealized behavior:
    flatten() sorts by (timeline_start, clip.track_index), but
    Composition.add_clip() never actually sets clip.track_index to
    match the track it was added to - Clip.track_index stays at its
    default (0) for every clip regardless of which track holds it.
    In practice flatten() therefore only ever sorts by timeline_start.
    """
    comp = Composition()
    comp.add_track(Track(name="V1"))
    comp.add_track(Track(name="V2"))

    clip_in_track_2 = _clip(asset, 5, 5)
    comp.add_clip(clip_in_track_2, track_index=1)

    assert clip_in_track_2.track_index == 0  # not 1, despite being in track index 1


def test_flatten_sorts_by_timeline_start(asset: MediaAsset) -> None:
    comp = Composition()
    comp.add_track(Track(name="V1"))

    later = _clip(asset, 20, 5)
    earlier = _clip(asset, 0, 5)
    comp.add_clip(later, track_index=0)
    comp.add_clip(earlier, track_index=0)

    flattened = comp.flatten()

    assert [c.timeline_start for c in flattened] == [0.0, 20.0]


def test_clear() -> None:
    comp = Composition()
    comp.add_track(Track(name="V1"))

    comp.clear()

    assert comp.track_count == 0


def test_duplicate_gets_new_id_and_is_independent() -> None:
    comp = Composition(name="Intro")
    comp.add_track(Track(name="V1"))

    dup = comp.duplicate()

    assert dup.id != comp.id
    assert dup.track_count == 1

    dup.add_track(Track(name="V2"))
    assert comp.track_count == 1


def test_is_vertical() -> None:
    comp = Composition(width=1080, height=1920)
    assert comp.is_vertical is True
    assert comp.aspect_ratio == pytest.approx(1080 / 1920, rel=1e-3)


def test_summary_and_len() -> None:
    comp = Composition(name="Intro")
    comp.add_track(Track(name="V1"))

    summary = comp.summary()

    assert summary["name"] == "Intro"
    assert summary["tracks"] == 1
    assert len(comp) == comp.clip_count
