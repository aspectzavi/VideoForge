"""
Fast, pytest-based tests for SelectionManager (editor/selection.py).

Distinct from media/selection.py's Selection - this class actually
mutates clip.selected as a side effect and is wired into Editor as
editor.selection.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from videoforge.editor.selection import SelectionManager
from videoforge.media.asset import MediaAsset
from videoforge.media.clip import Clip
from videoforge.media.effect import Effect
from videoforge.media.marker import Marker
from videoforge.media.overlay import Overlay
from videoforge.media.track import Track

SAMPLE_MEDIA = Path("tests/sample_media/input.mp4")


@pytest.fixture
def clip() -> Clip:
    asset = MediaAsset.load(SAMPLE_MEDIA)
    c = Clip(asset=asset)
    c.trim(0, 10)
    return c


@pytest.fixture
def manager() -> SelectionManager:
    return SelectionManager()


def test_select_clip_marks_clip_selected(manager: SelectionManager, clip: Clip) -> None:
    manager.select_clip(clip)

    assert clip.selected is True
    assert clip in manager.clips
    assert manager.is_clip_selected(clip) is True


def test_select_clip_not_additive_clears_previous(
    manager: SelectionManager, clip: Clip
) -> None:
    other = clip.clone()
    manager.select_clip(clip)

    manager.select_clip(other, additive=False)

    assert clip.selected is False
    assert clip not in manager.clips
    assert other in manager.clips


def test_deselect_clip(manager: SelectionManager, clip: Clip) -> None:
    manager.select_clip(clip)
    manager.deselect_clip(clip)

    assert clip.selected is False
    assert clip not in manager.clips


def test_toggle_clip(manager: SelectionManager, clip: Clip) -> None:
    manager.toggle_clip(clip)
    assert clip in manager.clips

    manager.toggle_clip(clip)
    assert clip not in manager.clips


def test_clear_clips_deselects_everything(manager: SelectionManager, clip: Clip) -> None:
    manager.select_clip(clip)
    manager.clear_clips()

    assert clip.selected is False
    assert manager.clip_count == 0


def test_select_track_overlay_marker_effect(manager: SelectionManager) -> None:
    track = Track(name="V1")
    overlay = Overlay()
    marker = Marker()
    effect = Effect(name="Blur")

    manager.select_track(track)
    manager.select_overlay(overlay)
    manager.select_marker(marker)
    manager.select_effect(effect)

    assert track in manager.tracks
    assert overlay in manager.overlays
    assert marker in manager.markers
    assert effect in manager.effects
    assert len(manager) == 4


def test_clear_clears_every_category(manager: SelectionManager, clip: Clip) -> None:
    manager.select_clip(clip)
    manager.select_track(Track(name="V1"))
    manager.select_overlay(Overlay())
    manager.select_marker(Marker())
    manager.select_effect(Effect(name="Blur"))

    manager.clear()

    assert manager.has_selection is False
    assert len(manager) == 0
    assert clip.selected is False


def test_has_selection_and_bool(manager: SelectionManager, clip: Clip) -> None:
    assert bool(manager) is False
    assert manager.has_selection is False

    manager.select_clip(clip)

    assert bool(manager) is True
    assert manager.has_selection is True
