"""
VideoForge Ripple Editing

Ripple editing shifts timeline contents while preserving
the relative spacing between clips.

Examples
--------
Insert clip
Delete clip
Extend trim
Close gap
"""

from __future__ import annotations

from videoforge.media.clip import Clip
from videoforge.media.timeline import Timeline


class RippleEditor:
    """
    Implements ripple editing operations.
    """

    def __init__(self, timeline: Timeline):
        self.timeline = timeline

    # ---------------------------------------------------------
    # Core Ripple
    # ---------------------------------------------------------

    def ripple(
        self,
        start_time: float,
        delta: float,
    ) -> None:
        """
        Shift every clip beginning at or after start_time.

        Positive delta moves clips forward.
        Negative delta moves clips backward.
        """

        if delta == 0:
            return

        for track in self.timeline.tracks:
            if track.locked:
                continue

            for clip in track.clips:
                if clip.locked:
                    continue

                if clip.timeline_start >= start_time:
                    clip.offset(delta)

            track._sort()

    # ---------------------------------------------------------
    # Gap Removal
    # ---------------------------------------------------------

    def close_gap(
        self,
        gap_start: float,
        gap_duration: float,
    ) -> None:
        """
        Remove a gap by moving later clips left.
        """

        if gap_duration <= 0:
            return

        self.ripple(
            gap_start + gap_duration,
            -gap_duration,
        )

    # ---------------------------------------------------------
    # Space Creation
    # ---------------------------------------------------------

    def create_space(
        self,
        position: float,
        duration: float,
    ) -> None:
        """
        Create empty timeline space.
        """

        if duration <= 0:
            return

        self.ripple(
            position,
            duration,
        )

    # ---------------------------------------------------------
    # Ripple Delete
    # ---------------------------------------------------------

    def ripple_delete(
        self,
        clip: Clip,
    ) -> bool:
        """
        Delete a clip and close the resulting gap.
        """

        for track in self.timeline.tracks:
            if clip not in track.clips:
                continue

            start = clip.timeline_start
            duration = clip.duration

            track.remove_clip(clip)

            self.close_gap(
                start,
                duration,
            )

            return True

        return False

    # ---------------------------------------------------------
    # Ripple Insert
    # ---------------------------------------------------------

    def ripple_insert(
        self,
        clip: Clip,
        track_index: int,
    ) -> Clip:
        """
        Insert a clip while pushing later clips forward.
        """

        track = self.timeline.tracks[track_index]

        self.create_space(
            clip.timeline_start,
            clip.duration,
        )

        track.add_clip(clip)

        return clip
