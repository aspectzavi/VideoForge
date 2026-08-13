"""
VideoForge Timeline Utilities

Shared helper functions for timeline editing.

These utilities are intentionally stateless and are reused by
move.py, trim.py, ripple.py, overwrite.py, insert.py and other
editing operations.
"""

from __future__ import annotations

from videoforge.media.clip import Clip
from videoforge.media.timeline import Timeline
from videoforge.media.track import Track


class TimelineUtils:
    """
    Stateless timeline utility service.
    """

    # ==========================================================
    # Clip Utilities
    # ==========================================================

    @staticmethod
    def sort_track(
        track: Track,
    ) -> None:
        """
        Sort clips in timeline order.
        """

        track.clips.sort(
            key=lambda clip: clip.timeline_start,
        )

    @classmethod
    def sort_timeline(
        cls,
        timeline: Timeline,
    ) -> None:
        """
        Sort every track.
        """

        for track in timeline.tracks:
            cls.sort_track(track)

    # ==========================================================
    # Searching
    # ==========================================================

    @staticmethod
    def find_clip(
        timeline: Timeline,
        clip_id: str,
    ) -> Clip | None:
        """
        Find a clip by id.
        """

        for track in timeline.tracks:
            for clip in track.clips:
                if clip.id == clip_id:
                    return clip

        return None

    @staticmethod
    def find_track_of_clip(
        timeline: Timeline,
        clip: Clip,
    ) -> Track | None:
        """
        Return the track containing a clip.
        """

        for track in timeline.tracks:
            if clip in track.clips:
                return track

        return None

    # ==========================================================
    # Time
    # ==========================================================

    @staticmethod
    def timeline_duration(
        timeline: Timeline,
    ) -> float:
        """
        Compute timeline duration.
        """

        if not timeline.tracks:
            return 0.0

        return max(
            (track.duration for track in timeline.tracks),
            default=0.0,
        )

    # ==========================================================
    # Overlap
    # ==========================================================

    @staticmethod
    def clips_overlap(
        first: Clip,
        second: Clip,
    ) -> bool:
        """
        True if two clips overlap.
        """

        return (
            first.timeline_start < second.timeline_end
            and first.timeline_end > second.timeline_start
        )

    @classmethod
    def overlapping_clips(
        cls,
        track: Track,
        clip: Clip,
    ) -> list[Clip]:
        """
        Return clips overlapping another clip.
        """

        overlaps: list[Clip] = []

        for other in track.clips:
            if other.id == clip.id:
                continue

            if cls.clips_overlap(
                clip,
                other,
            ):
                overlaps.append(other)

        return overlaps

    @classmethod
    def has_overlap(
        cls,
        track: Track,
        clip: Clip,
    ) -> bool:
        """
        Check whether a clip overlaps.
        """

        return bool(
            cls.overlapping_clips(
                track,
                clip,
            )
        )

    # ==========================================================
    # Gaps
    # ==========================================================

    @classmethod
    def gap_after(
        cls,
        clip: Clip,
        track: Track,
    ) -> float:
        """
        Empty space immediately after a clip.
        """

        cls.sort_track(track)

        try:
            index = track.clips.index(clip)
        except ValueError:
            return 0.0

        if index == len(track.clips) - 1:
            return float("inf")

        next_clip = track.clips[index + 1]

        return max(
            0.0,
            next_clip.timeline_start - clip.timeline_end,
        )

    @classmethod
    def gap_before(
        cls,
        clip: Clip,
        track: Track,
    ) -> float:
        """
        Empty space before a clip.
        """

        cls.sort_track(track)

        try:
            index = track.clips.index(clip)
        except ValueError:
            return 0.0

        if index == 0:
            return clip.timeline_start

        previous = track.clips[index - 1]

        return max(
            0.0,
            clip.timeline_start - previous.timeline_end,
        )

    # ==========================================================
    # Validation
    # ==========================================================

    @staticmethod
    def ensure_clip_in_track(
        track: Track,
        clip: Clip,
    ) -> None:
        """
        Raise if clip is missing.
        """

        if clip not in track.clips:
            raise ValueError("Clip is not part of track.")

    @staticmethod
    def ensure_positive_time(
        seconds: float,
    ) -> None:
        """
        Validate timeline time.
        """

        if seconds < 0:
            raise ValueError("Timeline time cannot be negative.")

    # ==========================================================
    # Movement
    # ==========================================================

    @classmethod
    def move_clip(
        cls,
        clip: Clip,
        position: float,
    ) -> None:
        """
        Move a clip.
        """

        cls.ensure_positive_time(position)

        clip.move(position)

    @staticmethod
    def offset_clip(
        clip: Clip,
        delta: float,
    ) -> None:
        """
        Offset a clip.
        """

        clip.move(
            max(
                0.0,
                clip.timeline_start + delta,
            )
        )

    # ==========================================================
    # Ripple Helpers
    # ==========================================================

    @classmethod
    def ripple_track(
        cls,
        track: Track,
        start_time: float,
        delta: float,
    ) -> None:
        """
        Ripple every clip after a time.
        """

        for clip in track.clips:
            if clip.timeline_start >= start_time:
                clip.offset(delta)

        cls.sort_track(track)

    @classmethod
    def ripple_timeline(
        cls,
        timeline: Timeline,
        start_time: float,
        delta: float,
    ) -> None:
        """
        Ripple every track.
        """

        for track in timeline.tracks:
            cls.ripple_track(
                track,
                start_time,
                delta,
            )
