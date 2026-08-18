"""
VideoForge Editor

Main faÃ§ade for all timeline editing operations.
"""

from __future__ import annotations

from typing import Callable, TypeVar

from videoforge.editor.clipboard import Clipboard
from videoforge.editor.delete import DeleteEditor
from videoforge.editor.group import GroupManager
from videoforge.editor.history import History, LambdaCommand
from videoforge.editor.insert import InsertEngine
from videoforge.editor.move import MoveEngine
from videoforge.editor.overwrite import OverwriteEditor
from videoforge.editor.ripple import RippleEditor
from videoforge.editor.selection import SelectionManager
from videoforge.editor.snapping import SnapEngine
from videoforge.editor.split import SplitEditor
from videoforge.editor.timeline_utils import TimelineUtils
from videoforge.editor.trim import TrimEditor
from videoforge.editor.validator import TimelineValidator
from videoforge.media.clip import Clip
from videoforge.media.timeline import Timeline
from videoforge.media.track import Track

T = TypeVar("T")

# A per-track snapshot of clip identity/order plus each clip's mutable
# positioning fields, taken before a mutating edit so it can be
# restored verbatim on undo. This covers every edit Editor exposes
# (insert/overwrite/move/split/trim/ripple/delete all only add,
# remove, or reposition clips within existing tracks - none of them
# add or remove whole tracks), so one generic mechanism is correct for
# all of them rather than hand-writing an inverse per operation.
_ClipState = tuple[Clip, float, float, float | None, float]


def _snapshot_timeline(timeline: Timeline) -> list[tuple[Track, list[_ClipState]]]:
    # Track (a Pydantic model) is not hashable, so a dict keyed by
    # Track cannot be used - a list of (track, clip_states) pairs
    # preserves the same information and track order.
    return [
        (
            track,
            [
                (clip, clip.timeline_start, clip.source_start, clip.source_end, clip.speed)
                for clip in track.clips
            ],
        )
        for track in timeline.tracks
    ]


def _restore_timeline(snapshot: list[tuple[Track, list[_ClipState]]]) -> None:
    for track, clip_states in snapshot:
        track.clips = [state[0] for state in clip_states]

        for clip, timeline_start, source_start, source_end, speed in clip_states:
            clip.timeline_start = timeline_start
            clip.source_start = source_start
            clip.source_end = source_end
            clip.speed = speed



class Editor:
    """
    Main editor faÃ§ade.
    """

    def __init__(
        self,
        timeline: Timeline,
    ) -> None:

        self.timeline = timeline

        # -----------------------------------------------------
        # Services
        # -----------------------------------------------------

        self.clipboard = Clipboard()

        self.history = History()

        self.selection = SelectionManager()

        self.groups = GroupManager(timeline)

        self.snap = SnapEngine(timeline)

        self.validator = TimelineValidator()

        self.utils = TimelineUtils()

        # -----------------------------------------------------
        # Editing Engines
        # -----------------------------------------------------

        self.ripple_editor = RippleEditor(timeline)

        self.trim_editor = TrimEditor(timeline)

        self.delete_editor = DeleteEditor(timeline)

    # ==========================================================
    # History integration
    # ==========================================================

    def _execute_with_history(
        self,
        description: str,
        action: Callable[[], T],
    ) -> T:
        """
        Run a mutating action through self.history so it becomes
        undoable/redoable.

        A timeline-wide snapshot is taken before `action` runs and
        restored verbatim on undo; redo simply re-runs `action` against
        that restored (pre-action) state, which reproduces the original
        result exactly since none of Editor's edits are randomized or
        depend on wall-clock time.
        """

        before = _snapshot_timeline(self.timeline)
        result_box: list[T] = []

        def _do() -> None:
            result_box.append(action())

        def _undo() -> None:
            _restore_timeline(before)

        self.history.execute(
            LambdaCommand(do=_do, undo=_undo, description=description)
        )

        return result_box[0]

    # ==========================================================
    # Insert
    # ==========================================================

    def insert_clip(
        self,
        track: Track,
        clip: Clip,
        position: float,
    ) -> Clip:

        return self._execute_with_history(
            "Insert Clip",
            lambda: InsertEngine.insert_clip(track, clip, position),
        )

    # ==========================================================
    # Overwrite
    # ==========================================================

    def overwrite_clip(
        self,
        track: Track,
        clip: Clip,
        position: float,
    ) -> Clip:

        return self._execute_with_history(
            "Overwrite Clip",
            lambda: OverwriteEditor.overwrite(track, clip, position),
        )

    # ==========================================================
    # Move
    # ==========================================================

    def move_clip(
        self,
        track: Track,
        clip: Clip,
        position: float,
    ) -> None:

        self._execute_with_history(
            "Move Clip",
            lambda: MoveEngine.move_clip(track, clip, position),
        )

    # ==========================================================
    # Split
    # ==========================================================

    def split_clip(
        self,
        track: Track,
        clip: Clip,
        time: float,
    ) -> tuple[Clip, Clip]:

        return self._execute_with_history(
            "Split Clip",
            lambda: SplitEditor.split(track, clip, time),
        )

    # ==========================================================
    # Trim
    # ==========================================================

    def trim_in(
        self,
        clip: Clip,
        amount: float,
    ) -> None:

        self._execute_with_history(
            "Trim In",
            lambda: self.trim_editor.trim_in(clip, amount),
        )

    def trim_out(
        self,
        clip: Clip,
        amount: float,
    ) -> None:

        self._execute_with_history(
            "Trim Out",
            lambda: self.trim_editor.trim_out(clip, amount),
        )

    def ripple_trim_in(
        self,
        clip: Clip,
        amount: float,
    ) -> None:

        self._execute_with_history(
            "Ripple Trim In",
            lambda: self.trim_editor.ripple_trim_in(clip, amount),
        )

    def ripple_trim_out(
        self,
        clip: Clip,
        amount: float,
    ) -> None:

        self._execute_with_history(
            "Ripple Trim Out",
            lambda: self.trim_editor.ripple_trim_out(clip, amount),
        )

    # ==========================================================
    # Ripple
    # ==========================================================

    def ripple(
        self,
        start_time: float,
        delta: float,
    ) -> None:

        self._execute_with_history(
            "Ripple",
            lambda: self.ripple_editor.ripple(start_time, delta),
        )

    # ==========================================================
    # Delete
    # ==========================================================

    def delete_clip(
        self,
        clip: Clip,
    ) -> bool:

        return self._execute_with_history(
            "Delete Clip",
            lambda: self.delete_editor.delete_clip(clip),
        )

    def ripple_delete(
        self,
        clip: Clip,
    ) -> bool:

        return self._execute_with_history(
            "Ripple Delete",
            lambda: self.delete_editor.ripple_delete(clip),
        )

    # ==========================================================
    # Validation
    # ==========================================================

    def validate(self):

        return self.validator.validate(
            self.timeline,
        )

    # ==========================================================
    # Timeline
    # ==========================================================

    def clear(self) -> None:

        self.timeline.clear()

    # ==========================================================
    # Helpers
    # ==========================================================

    @property
    def duration(self) -> float:

        return self.timeline.duration

    @property
    def clip_count(self) -> int:

        return self.timeline.clip_count

    @property
    def track_count(self) -> int:

        return self.timeline.track_count

    # ==========================================================
    # Representation
    # ==========================================================

    def __repr__(self) -> str:

        return (
            "Editor("
            f"tracks={self.track_count}, "
            f"clips={self.clip_count}, "
            f"duration={self.duration:.2f}s)"
        )
