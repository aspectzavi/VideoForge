"""
VideoForge Delete Engine

Implements timeline deletion operations.

Supports

- Delete clip
- Delete multiple clips
- Ripple delete
- Delete track
"""

from __future__ import annotations

from videoforge.media.clip import Clip
from videoforge.media.timeline import Timeline
from videoforge.media.track import Track


class DeleteEditor:
    """
    Timeline deletion utilities.
    """

    def __init__(
        self,
        timeline: Timeline,
    ):
        self.timeline = timeline

    # ==========================================================
    # Delete Clip
    # ==========================================================

    def delete_clip(
        self,
        clip: Clip,
    ) -> bool:
        """
        Delete a clip without rippling.

        Returns
        -------
        True if deleted.
        """

        for track in self.timeline.tracks:
            if clip in track.clips:
                track.remove_clip(clip)
                return True

        return False

    # ==========================================================
    # Ripple Delete
    # ==========================================================

    def ripple_delete(
        self,
        clip: Clip,
    ) -> bool:
        """
        Delete a clip and close the gap.
        """

        start = clip.timeline_start
        duration = clip.duration

        if not self.delete_clip(clip):
            return False

        self.timeline.ripple(
            start + duration,
            -duration,
        )

        return True

    # ==========================================================
    # Delete Multiple
    # ==========================================================

    def delete_clips(
        self,
        clips: list[Clip],
    ) -> int:
        """
        Delete multiple clips.

        Returns
        -------
        Number deleted.
        """

        deleted = 0

        for clip in list(clips):
            if self.delete_clip(clip):
                deleted += 1

        return deleted

    # ==========================================================
    # Ripple Delete Multiple
    # ==========================================================

    def ripple_delete_clips(
        self,
        clips: list[Clip],
    ) -> int:
        """
        Ripple delete several clips.

        Clips are processed from left to right.
        """

        ordered = sorted(
            clips,
            key=lambda c: c.timeline_start,
        )

        deleted = 0

        for clip in ordered:
            if self.ripple_delete(clip):
                deleted += 1

        return deleted

    # ==========================================================
    # Delete Track
    # ==========================================================

    def delete_track(
        self,
        track: Track,
    ) -> bool:
        """
        Remove an entire track.
        """

        if track not in self.timeline.tracks:
            return False

        self.timeline.remove_track(track)

        return True

    # ==========================================================
    # Delete Empty Tracks
    # ==========================================================

    def delete_empty_tracks(
        self,
    ) -> int:
        """
        Remove every empty track.

        Returns
        -------
        Number removed.
        """

        removed = 0

        for track in list(self.timeline.tracks):
            if track.is_empty:
                self.timeline.remove_track(track)
                removed += 1

        return removed

    # ==========================================================
    # Clear Timeline
    # ==========================================================

    def clear(
        self,
    ) -> None:
        """
        Remove every editable object.
        """

        self.timeline.clear()
