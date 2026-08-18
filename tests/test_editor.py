"""
Fast, pytest-based tests for the Editor façade
(src/videoforge/editor/editor.py).

Covers the flat method API and, importantly, the History
integration: every mutating method must be undoable/redoable via
editor.history, which was previously constructed but never wired to
anything.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from videoforge.editor.editor import Editor
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
    t.add_clip(_clip(asset, 0, 20, 0))
    return t


@pytest.fixture
def timeline(track: Track) -> Timeline:
    tl = Timeline()
    tl.add_track(track)
    return tl


@pytest.fixture
def editor(timeline: Timeline) -> Editor:
    return Editor(timeline)


# ---------------------------------------------------------------------
# Construction / helpers
# ---------------------------------------------------------------------


def test_editor_helpers_reflect_timeline(editor: Editor, timeline: Timeline) -> None:
    assert editor.duration == timeline.duration
    assert editor.clip_count == timeline.clip_count
    assert editor.track_count == timeline.track_count


def test_editor_clear_empties_timeline(editor: Editor, timeline: Timeline) -> None:
    editor.clear()
    assert timeline.is_empty is True


def test_editor_history_starts_empty(editor: Editor) -> None:
    assert editor.history.can_undo is False
    assert editor.history.can_redo is False


# ---------------------------------------------------------------------
# Insert (+ history)
# ---------------------------------------------------------------------


def test_insert_clip_adds_to_track(
    editor: Editor, track: Track, asset: MediaAsset
) -> None:
    new_clip = _clip(asset, 0, 5, 100)

    editor.insert_clip(track, new_clip, 25.0)

    assert track.clip_count == 2
    assert new_clip.timeline_start == pytest.approx(25.0)


def test_insert_clip_is_undoable_and_redoable(
    editor: Editor, track: Track, asset: MediaAsset
) -> None:
    new_clip = _clip(asset, 0, 5, 100)

    editor.insert_clip(track, new_clip, 25.0)
    assert track.clip_count == 2
    assert editor.history.can_undo is True

    editor.history.undo()
    assert track.clip_count == 1
    assert editor.history.can_redo is True

    editor.history.redo()
    assert track.clip_count == 2
    assert new_clip in track.clips


# ---------------------------------------------------------------------
# Overwrite (+ history)
# ---------------------------------------------------------------------


def test_overwrite_clip_replaces_overlap(
    editor: Editor, track: Track, asset: MediaAsset
) -> None:
    original = track.clips[0]
    overwriting = _clip(asset, 0, 5, 100)

    editor.overwrite_clip(track, overwriting, 5.0)

    # overwriting spans 5..10, which overlaps the original's 0..20 -
    # OverwriteEditor drops any overlapping clip entirely (no partial
    # trimming), so only the new clip remains.
    assert track.clips == [overwriting]
    assert original not in track.clips


def test_overwrite_clip_is_undoable(
    editor: Editor, track: Track, asset: MediaAsset
) -> None:
    original_clips = list(track.clips)
    overwriting = _clip(asset, 0, 5, 100)

    editor.overwrite_clip(track, overwriting, 5.0)
    editor.history.undo()

    assert track.clips == original_clips


# ---------------------------------------------------------------------
# Move (+ history)
# ---------------------------------------------------------------------


def test_move_clip_repositions(editor: Editor, track: Track) -> None:
    clip = track.clips[0]

    editor.move_clip(track, clip, 50.0)

    assert clip.timeline_start == pytest.approx(50.0)


def test_move_clip_is_undoable_and_redoable(editor: Editor, track: Track) -> None:
    clip = track.clips[0]

    editor.move_clip(track, clip, 50.0)
    editor.history.undo()
    assert clip.timeline_start == pytest.approx(0.0)

    editor.history.redo()
    assert clip.timeline_start == pytest.approx(50.0)


# ---------------------------------------------------------------------
# Split (+ history)
# ---------------------------------------------------------------------


def test_split_clip_produces_two_clips(editor: Editor, track: Track) -> None:
    clip = track.clips[0]

    left, right = editor.split_clip(track, clip, 10.0)

    assert track.clip_count == 2
    assert left.timeline_end == pytest.approx(10.0)
    assert right.timeline_start == pytest.approx(10.0)


def test_split_clip_is_undoable_restores_original_object(
    editor: Editor, track: Track
) -> None:
    clip = track.clips[0]

    editor.split_clip(track, clip, 10.0)
    assert track.clip_count == 2

    editor.history.undo()

    assert track.clip_count == 1
    assert track.clips[0] is clip  # the exact original object, not a copy


def test_split_clip_redo_reproduces_the_split(editor: Editor, track: Track) -> None:
    clip = track.clips[0]

    editor.split_clip(track, clip, 10.0)
    editor.history.undo()
    editor.history.redo()

    assert track.clip_count == 2
    assert [round(c.timeline_start, 2) for c in track.clips] == [0.0, 10.0]


# ---------------------------------------------------------------------
# Trim (+ history)
# ---------------------------------------------------------------------


def test_trim_in_shortens_from_the_start(editor: Editor, track: Track) -> None:
    clip = track.clips[0]  # source 0..20, timeline_start 0

    editor.trim_in(clip, 5.0)

    assert clip.source_start == pytest.approx(5.0)
    assert clip.timeline_start == pytest.approx(5.0)
    assert clip.duration == pytest.approx(15.0)


def test_trim_in_is_undoable(editor: Editor, track: Track) -> None:
    clip = track.clips[0]

    editor.trim_in(clip, 5.0)
    editor.history.undo()

    assert clip.source_start == pytest.approx(0.0)
    assert clip.timeline_start == pytest.approx(0.0)


def test_trim_out_shortens_from_the_end(editor: Editor, track: Track) -> None:
    clip = track.clips[0]  # source 0..20

    editor.trim_out(clip, -5.0)

    assert clip.source_end == pytest.approx(15.0)


def test_trim_out_is_undoable(editor: Editor, track: Track) -> None:
    clip = track.clips[0]
    original_end = clip.source_end

    editor.trim_out(clip, -5.0)
    editor.history.undo()

    assert clip.source_end == pytest.approx(original_end)


def test_ripple_trim_in_shifts_later_clips(
    editor: Editor, track: Track, asset: MediaAsset
) -> None:
    first = track.clips[0]  # 0..20
    second = _clip(asset, 0, 10, 20.0)  # 20..30
    track.add_clip(second)

    editor.ripple_trim_in(first, 5.0)  # first shrinks by 5 (now 5..20)

    assert first.timeline_start == pytest.approx(5.0)
    assert second.timeline_start == pytest.approx(15.0)  # shifted back by 5


def test_ripple_trim_in_is_undoable(
    editor: Editor, track: Track, asset: MediaAsset
) -> None:
    first = track.clips[0]
    second = _clip(asset, 0, 10, 20.0)
    track.add_clip(second)

    editor.ripple_trim_in(first, 5.0)
    editor.history.undo()

    assert first.timeline_start == pytest.approx(0.0)
    assert second.timeline_start == pytest.approx(20.0)


# ---------------------------------------------------------------------
# Ripple (+ history)
# ---------------------------------------------------------------------


def test_ripple_shifts_clips_at_or_after_start_time(
    editor: Editor, track: Track, asset: MediaAsset
) -> None:
    first = track.clips[0]  # 0..20
    second = _clip(asset, 0, 10, 20.0)  # 20..30
    track.add_clip(second)

    editor.ripple(20.0, 5.0)

    assert first.timeline_start == pytest.approx(0.0)  # before start_time
    assert second.timeline_start == pytest.approx(25.0)  # shifted


def test_ripple_is_undoable(editor: Editor, track: Track, asset: MediaAsset) -> None:
    second = _clip(asset, 0, 10, 20.0)
    track.add_clip(second)

    editor.ripple(20.0, 5.0)
    editor.history.undo()

    assert second.timeline_start == pytest.approx(20.0)


# ---------------------------------------------------------------------
# Delete (+ history)
# ---------------------------------------------------------------------


def test_delete_clip_removes_without_rippling(
    editor: Editor, track: Track, asset: MediaAsset
) -> None:
    first = track.clips[0]
    second = _clip(asset, 0, 10, 20.0)
    track.add_clip(second)

    result = editor.delete_clip(first)

    assert result is True
    assert first not in track.clips
    assert second.timeline_start == pytest.approx(20.0)  # unchanged, no ripple


def test_delete_clip_returns_false_for_unknown_clip(
    editor: Editor, asset: MediaAsset
) -> None:
    stray = _clip(asset, 0, 5, 0)
    assert editor.delete_clip(stray) is False


def test_delete_clip_is_undoable(editor: Editor, track: Track) -> None:
    clip = track.clips[0]

    editor.delete_clip(clip)
    assert track.clip_count == 0

    editor.history.undo()

    assert track.clip_count == 1
    assert track.clips[0] is clip


def test_ripple_delete_closes_the_gap(
    editor: Editor, track: Track, asset: MediaAsset
) -> None:
    first = track.clips[0]  # 0..20
    second = _clip(asset, 0, 10, 20.0)  # 20..30
    track.add_clip(second)

    result = editor.ripple_delete(first)

    assert result is True
    assert first not in track.clips
    assert second.timeline_start == pytest.approx(0.0)  # gap closed


def test_ripple_delete_is_undoable(
    editor: Editor, track: Track, asset: MediaAsset
) -> None:
    first = track.clips[0]
    second = _clip(asset, 0, 10, 20.0)
    track.add_clip(second)

    editor.ripple_delete(first)
    editor.history.undo()

    assert track.clip_count == 2
    assert first in track.clips
    assert second.timeline_start == pytest.approx(20.0)


# ---------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------


def test_validate_delegates_to_validator(editor: Editor) -> None:
    result = editor.validate()
    assert result is not None


# ---------------------------------------------------------------------
# History stack integrity
# ---------------------------------------------------------------------


def test_new_edit_after_undo_clears_redo_stack(editor: Editor, track: Track) -> None:
    clip = track.clips[0]

    editor.move_clip(track, clip, 10.0)
    editor.history.undo()
    assert editor.history.can_redo is True

    editor.move_clip(track, clip, 20.0)

    # a fresh edit after undo invalidates the old redo branch
    assert editor.history.can_redo is False


def test_multiple_edits_undo_in_reverse_order(editor: Editor, track: Track) -> None:
    clip = track.clips[0]

    editor.move_clip(track, clip, 10.0)
    editor.move_clip(track, clip, 20.0)
    editor.move_clip(track, clip, 30.0)

    editor.history.undo()
    assert clip.timeline_start == pytest.approx(20.0)

    editor.history.undo()
    assert clip.timeline_start == pytest.approx(10.0)

    editor.history.undo()
    assert clip.timeline_start == pytest.approx(0.0)

    assert editor.history.can_undo is False
