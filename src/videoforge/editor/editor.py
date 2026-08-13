"""
VideoForge Editor

Main façade for all timeline editing operations.
"""

from __future__ import annotations

from videoforge.editor.clipboard import Clipboard
from videoforge.editor.delete import DeleteEditor
from videoforge.editor.group import GroupManager
from videoforge.editor.history import History
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


class Editor:
    """
    Main editor façade.
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
    # Insert
    # ==========================================================

    def insert_clip(
        self,
        track: Track,
        clip: Clip,
        position: float,
    ) -> Clip:

        return InsertEngine.insert_clip(
            track,
            clip,
            position,
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

        return OverwriteEditor.overwrite(
            track,
            clip,
            position,
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

        MoveEngine.move_clip(
            track,
            clip,
            position,
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

        return SplitEditor.split(
            track,
            clip,
            time,
        )

    # ==========================================================
    # Trim
    # ==========================================================

    def trim_in(
        self,
        clip: Clip,
        amount: float,
    ) -> None:

        self.trim_editor.trim_in(
            clip,
            amount,
        )

    def trim_out(
        self,
        clip: Clip,
        amount: float,
    ) -> None:

        self.trim_editor.trim_out(
            clip,
            amount,
        )

    def ripple_trim_in(
        self,
        clip: Clip,
        amount: float,
    ) -> None:

        self.trim_editor.ripple_trim_in(
            clip,
            amount,
        )

    def ripple_trim_out(
        self,
        clip: Clip,
        amount: float,
    ) -> None:

        self.trim_editor.ripple_trim_out(
            clip,
            amount,
        )

    # ==========================================================
    # Ripple
    # ==========================================================

    def ripple(
        self,
        start_time: float,
        delta: float,
    ) -> None:

        self.ripple_editor.ripple(
            start_time,
            delta,
        )

    # ==========================================================
    # Delete
    # ==========================================================

    def delete_clip(
        self,
        clip: Clip,
    ) -> bool:

        return self.delete_editor.delete_clip(clip)

    def ripple_delete(
        self,
        clip: Clip,
    ) -> bool:

        return self.delete_editor.ripple_delete(clip)

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
