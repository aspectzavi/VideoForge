"""
VideoForge Split Engine

Splits clips into two independent clips.

Example

Before

|--------- Clip ---------|

Split at 4.5 s

After

|---- Clip A ----|---- Clip B ----|
"""

from __future__ import annotations

from videoforge.media.clip import Clip
from videoforge.media.track import Track


class SplitEditor:
    """
    Clip splitting utilities.
    """

    # ==========================================================
    # Split Clip
    # ==========================================================

    @staticmethod
    def split(
        track: Track,
        clip: Clip,
        timeline_time: float,
    ) -> tuple[Clip, Clip]:
        """
        Split a clip at an absolute timeline position.

        Returns
        -------
        (left_clip, right_clip)
        """

        if timeline_time <= clip.timeline_start or timeline_time >= clip.timeline_end:
            raise ValueError("Split position must be inside the clip.")

        # -----------------------------------------------------
        # Calculate source position
        # -----------------------------------------------------

        offset = timeline_time - clip.timeline_start

        source_split = clip.source_start + (offset * clip.speed)

        # -----------------------------------------------------
        # Duplicate clip
        # -----------------------------------------------------

        right = clip.clone()

        # -----------------------------------------------------
        # Left clip
        # -----------------------------------------------------

        clip.source_end = source_split

        # -----------------------------------------------------
        # Right clip
        # -----------------------------------------------------

        right.source_start = source_split

        right.timeline_start = timeline_time

        # -----------------------------------------------------
        # Replace in track
        # -----------------------------------------------------

        index = track.clips.index(clip)

        track.clips.insert(
            index + 1,
            right,
        )

        track.clips.sort(key=lambda c: c.timeline_start)

        return clip, right

    # ==========================================================
    # Split Multiple Clips
    # ==========================================================

    @staticmethod
    def split_many(
        track: Track,
        clips: list[Clip],
        timeline_time: float,
    ) -> list[tuple[Clip, Clip]]:
        """
        Split every clip intersecting the
        supplied timeline position.
        """

        results: list[tuple[Clip, Clip]] = []

        for clip in list(clips):
            if clip.timeline_start < timeline_time < clip.timeline_end:
                results.append(
                    SplitEditor.split(
                        track,
                        clip,
                        timeline_time,
                    )
                )

        return results

    # ==========================================================
    # Split At Playhead
    # ==========================================================

    @staticmethod
    def split_at_playhead(
        track: Track,
        playhead: float,
    ) -> list[tuple[Clip, Clip]]:
        """
        Split every clip crossing the playhead.
        """

        results: list[tuple[Clip, Clip]] = []

        for clip in list(track.clips):
            if clip.timeline_start < playhead < clip.timeline_end:
                results.append(
                    SplitEditor.split(
                        track,
                        clip,
                        playhead,
                    )
                )

        return results
