"""
VideoForge Insert Engine

Implements insert editing.

Insert editing shifts existing clips to the right to create
space for the inserted clip without overwriting any media.
"""

from __future__ import annotations

from videoforge.media.clip import Clip
from videoforge.media.track import Track


class InsertEngine:
    """
    Insert editing utilities.
    """

    # ---------------------------------------------------------
    # Insert clip
    # ---------------------------------------------------------

    @staticmethod
    def insert_clip(
        track: Track,
        clip: Clip,
        position: float,
    ) -> Clip:
        """
        Insert a clip at the specified timeline position.

        Existing clips at or after the insertion point are
        moved forward by the duration of the inserted clip.
        """

        duration = clip.duration

        # Ripple existing clips
        for existing in track.clips:
            if existing.timeline_start >= position:
                existing.offset(duration)

        # Position new clip
        clip.move(position)

        # Add clip
        track.add_clip(clip)

        track.clips.sort(key=lambda c: c.timeline_start)

        return clip

    # ---------------------------------------------------------
    # Insert multiple clips
    # ---------------------------------------------------------

    @staticmethod
    def insert_clips(
        track: Track,
        clips: list[Clip],
        position: float,
    ) -> list[Clip]:
        """
        Insert multiple clips sequentially.
        """

        current = position

        for clip in clips:
            InsertEngine.insert_clip(
                track,
                clip,
                current,
            )

            current += clip.duration

        return clips

    # ---------------------------------------------------------
    # Insert gap
    # ---------------------------------------------------------

    @staticmethod
    def insert_gap(
        track: Track,
        position: float,
        duration: float,
    ) -> None:
        """
        Insert empty space into a track.

        Every clip beginning at or after the specified
        position is shifted right.
        """

        if duration <= 0:
            return

        for clip in track.clips:
            if clip.timeline_start >= position:
                clip.offset(duration)

        track.clips.sort(key=lambda c: c.timeline_start)

    # ---------------------------------------------------------
    # Insert at playhead
    # ---------------------------------------------------------

    @staticmethod
    def insert_at_playhead(
        track: Track,
        clip: Clip,
        playhead: float,
    ) -> Clip:
        """
        Convenience wrapper.
        """

        return InsertEngine.insert_clip(
            track,
            clip,
            playhead,
        )
