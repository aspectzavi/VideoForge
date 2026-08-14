"""
Fast, pytest-based tests for Selection.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from videoforge.media.asset import MediaAsset
from videoforge.media.clip import Clip
from videoforge.media.marker import Marker
from videoforge.media.selection import Selection
from videoforge.media.track import Track

SAMPLE_MEDIA = Path("tests/sample_media/input.mp4")


@pytest.fixture
def asset() -> MediaAsset:
    return MediaAsset.load(SAMPLE_MEDIA)


@pytest.fixture
def clip(asset: MediaAsset) -> Clip:
    c = Clip(asset=asset)
    c.trim(0, 10)
    return c


def test_selection_is_empty_by_default() -> None:
    selection = Selection()

    assert selection.is_empty is True
    assert selection.total_count == 0
    assert len(selection) == 0
    assert selection.has_clips is False
    assert selection.first_clip is None


# ---------------------------------------------------------------------
# Clip selection
# ---------------------------------------------------------------------


def test_selection_select_clip_replaces_by_default(
    asset: MediaAsset, clip: Clip
) -> None:
    other = Clip(asset=asset)
    other.trim(0, 5)

    selection = Selection()
    selection.select_clip(clip)
    selection.select_clip(other)  # append=False -> replaces

    assert selection.clips == [other]
    assert selection.clip_count == 1


def test_selection_select_clip_append(asset: MediaAsset, clip: Clip) -> None:
    other = Clip(asset=asset)
    other.trim(0, 5)

    selection = Selection()
    selection.select_clip(clip, append=True)
    selection.select_clip(other, append=True)

    assert selection.clips == [clip, other]
    assert selection.clip_count == 2


def test_selection_select_clip_does_not_duplicate(clip: Clip) -> None:
    selection = Selection()
    selection.select_clip(clip, append=True)
    selection.select_clip(clip, append=True)  # same clip again

    assert selection.clips == [clip]


def test_selection_deselect_clip(clip: Clip) -> None:
    selection = Selection()
    selection.select_clip(clip)
    selection.deselect_clip(clip)

    assert selection.clips == []
    assert selection.has_clips is False

    # deselecting something not selected is a no-op, not an error
    selection.deselect_clip(clip)


# ---------------------------------------------------------------------
# Track / marker / asset selection follow the same pattern
# ---------------------------------------------------------------------


def test_selection_select_track() -> None:
    selection = Selection()
    track = Track(name="V1")

    selection.select_track(track)

    assert selection.tracks == [track]
    assert selection.has_tracks is True
    assert selection.first_track is track

    selection.deselect_track(track)
    assert selection.tracks == []


def test_selection_select_marker() -> None:
    selection = Selection()
    marker = Marker(name="Chapter 1")

    selection.select_marker(marker)

    assert selection.markers == [marker]
    assert selection.has_markers is True
    assert selection.first_marker is marker

    selection.deselect_marker(marker)
    assert selection.markers == []


def test_selection_select_asset(asset: MediaAsset) -> None:
    selection = Selection()

    selection.select_asset(asset)

    assert selection.assets == [asset]
    assert selection.has_assets is True
    assert selection.first_asset is asset

    selection.deselect_asset(asset)
    assert selection.assets == []


# ---------------------------------------------------------------------
# Mixed selection / clear / total_count / repr
# ---------------------------------------------------------------------


def test_selection_total_count_across_all_kinds(
    asset: MediaAsset, clip: Clip
) -> None:
    selection = Selection()
    selection.select_clip(clip, append=True)
    selection.select_track(Track(name="V1"), append=True)
    selection.select_marker(Marker(), append=True)
    selection.select_asset(asset, append=True)

    assert selection.total_count == 4
    assert len(selection) == 4
    assert selection.is_empty is False


def test_selection_clear_resets_everything(asset: MediaAsset, clip: Clip) -> None:
    selection = Selection()
    selection.select_clip(clip, append=True)
    selection.select_track(Track(name="V1"), append=True)
    selection.select_marker(Marker(), append=True)
    selection.select_asset(asset, append=True)

    selection.clear()

    assert selection.is_empty is True
    assert selection.total_count == 0
    assert selection.clips == []
    assert selection.tracks == []
    assert selection.markers == []
    assert selection.assets == []
