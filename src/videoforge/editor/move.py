"""
VideoForge Move Engine

Implements clip movement operations.

Responsibilities
----------------
- Move clips on the timeline
- Move between tracks
- Move multiple clips
- Preserve ordering
"""

from __future__ import annotations

from videoforge.media.clip import Clip
from videoforge.media.timeline import Timeline
from videoforge.media.track import Track


class MoveEngine:
    """
    Timeline movement utilities.
    """

    # ---------------------------------------------------------
    # Move inside same track
    # ---------------------------------------------------------

    @staticmethod
    def move_clip(
        track: Track,
        clip: Clip,
        new_time: float,
    ) -> Clip:
        """
        Move a clip to a new timeline position.
        """

        clip.move(new_time)

        track.clips.sort(key=lambda c: c.timeline_start)

        return clip

    # ---------------------------------------------------------
    # Move to another track
    # ---------------------------------------------------------

    @staticmethod
    def move_to_track(
        timeline: Timeline,
        clip: Clip,
        destination: Track,
        new_time: float,
    ) -> Clip:
        """
        Move clip between tracks.
        """

        # remove from current track

        for track in timeline.tracks:
            if clip in track.clips:
                track.remove_clip(clip)
                break

        clip.move(new_time)

        destination.add_clip(clip)

        return clip

    # ---------------------------------------------------------
    # Offset
    # ---------------------------------------------------------

    @staticmethod
    def offset(
        clips: list[Clip],
        seconds: float,
    ) -> None:
        """
        Offset multiple clips.
        """

        for clip in clips:
            clip.offset(seconds)

    # ---------------------------------------------------------
    # Align
    # ---------------------------------------------------------

    @staticmethod
    def align_left(
        clips: list[Clip],
    ) -> None:
        """
        Align all clips to earliest start.
        """

        if not clips:
            return

        first = min(clip.timeline_start for clip in clips)

        for clip in clips:
            clip.move(first)

    # ---------------------------------------------------------
    # Nudge
    # ---------------------------------------------------------

    @staticmethod
    def nudge_left(
        clip: Clip,
        amount: float,
    ) -> None:
        clip.offset(-amount)

    @staticmethod
    def nudge_right(
        clip: Clip,
        amount: float,
    ) -> None:
        clip.offset(amount)

    # ---------------------------------------------------------
    # Snap
    # ---------------------------------------------------------

    @staticmethod
    def snap_to(
        clip: Clip,
        time: float,
    ) -> None:
        """
        Snap clip to exact timeline position.
        """

        clip.move(time)
