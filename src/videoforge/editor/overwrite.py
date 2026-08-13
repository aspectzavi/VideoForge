"""
VideoForge Overwrite Editing

Overwrite editing replaces timeline content without changing
the overall timeline length.

Example

Existing

| Clip A | Clip B | Clip C |

Overwrite Clip X over Clip B

Result

| Clip A | Clip X | Clip C |
"""

from __future__ import annotations

from videoforge.media.clip import Clip
from videoforge.media.track import Track


class OverwriteEditor:
    """
    Performs overwrite edits on a track.
    """

    @staticmethod
    def overwrite(
        track: Track,
        clip: Clip,
        position: float,
    ) -> Clip:
        """
        Insert a clip by replacing any overlapping clips.

        Timeline length is unchanged.
        """

        clip.move(position)

        clip_start = clip.timeline_start
        clip_end = clip.timeline_end

        remaining: list[Clip] = []

        for existing in track.clips:
            if existing.id == clip.id:
                continue

            overlap = (
                clip_start < existing.timeline_end
                and clip_end > existing.timeline_start
            )

            if not overlap:
                remaining.append(existing)

        remaining.append(clip)

        remaining.sort(key=lambda c: c.timeline_start)

        track.clips = remaining

        return clip

    @staticmethod
    def can_overwrite(
        track: Track,
        clip: Clip,
        position: float,
    ) -> bool:
        """
        Returns True if overwrite is allowed.

        Currently only checks whether the track is locked.
        """

        return not track.locked
