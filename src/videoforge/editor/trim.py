"""
VideoForge Trim Engine

Implements clip trimming.

Supported operations

- Trim In
- Trim Out
- Ripple Trim In
- Ripple Trim Out
"""

from __future__ import annotations

from videoforge.media.clip import Clip
from videoforge.media.timeline import Timeline


class TrimEditor:
    """
    Performs trimming operations.
    """

    def __init__(
        self,
        timeline: Timeline,
    ):
        self.timeline = timeline

    # ==========================================================
    # Trim In
    # ==========================================================

    def trim_in(
        self,
        clip: Clip,
        amount: float,
    ) -> None:
        """
        Trim from the beginning.

        Positive amount removes media.
        Negative amount extends media.
        """

        if amount == 0:
            return

        clip.source_start += amount
        clip.timeline_start += amount

        if clip.source_start < 0:
            clip.timeline_start -= clip.source_start
            clip.source_start = 0.0

        if clip.source_end is not None:
            clip.source_start = min(
                clip.source_start,
                clip.source_end,
            )

    # ==========================================================
    # Trim Out
    # ==========================================================

    def trim_out(
        self,
        clip: Clip,
        amount: float,
    ) -> None:
        """
        Trim the end of a clip.

        Positive amount extends.
        Negative amount shortens.
        """

        end = clip.source_end if clip.source_end is not None else clip.asset.duration

        end += amount

        end = max(
            clip.source_start,
            end,
        )

        clip.source_end = min(
            end,
            clip.asset.duration,
        )

    # ==========================================================
    # Ripple Trim In
    # ==========================================================

    def ripple_trim_in(
        self,
        clip: Clip,
        amount: float,
    ) -> None:
        """
        Trim the beginning and ripple
        every following clip.
        """

        old_duration = clip.duration

        self.trim_in(
            clip,
            amount,
        )

        delta = old_duration - clip.duration

        if delta == 0:
            return

        self.timeline.ripple(
            clip.timeline_end,
            -delta,
        )

    # ==========================================================
    # Ripple Trim Out
    # ==========================================================

    def ripple_trim_out(
        self,
        clip: Clip,
        amount: float,
    ) -> None:
        """
        Trim the end while rippling
        every later clip.
        """

        old_duration = clip.duration

        self.trim_out(
            clip,
            amount,
        )

        delta = old_duration - clip.duration

        if delta == 0:
            return

        self.timeline.ripple(
            clip.timeline_end,
            -delta,
        )

    # ==========================================================
    # Convenience
    # ==========================================================

    def set_in(
        self,
        clip: Clip,
        position: float,
    ) -> None:
        """
        Set absolute source in point.
        """

        self.trim_in(
            clip,
            position - clip.source_start,
        )

    def set_out(
        self,
        clip: Clip,
        position: float,
    ) -> None:
        """
        Set absolute source out point.
        """

        end = clip.source_end if clip.source_end is not None else clip.asset.duration

        self.trim_out(
            clip,
            position - end,
        )
