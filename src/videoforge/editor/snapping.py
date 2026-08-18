"""
VideoForge Snapping Engine

Provides magnetic snapping for timeline editing.

Supports snapping to

- Clip starts
- Clip ends
- Playhead
- Timeline markers

Future additions

- Grid snapping
- Audio beat snapping
- Keyframe snapping
- Guide snapping
"""

from __future__ import annotations

from videoforge.media.clip import Clip
from videoforge.media.timeline import Timeline


class SnapEngine:
    """
    Timeline snapping utilities.
    """

    def __init__(
        self,
        timeline: Timeline,
        threshold: float = 0.15,
    ):
        self.timeline = timeline
        self.threshold = threshold

    # ==========================================================
    # Snap Points
    # ==========================================================

    def snap_points(self) -> list[float]:
        """
        Return every available snap point.
        """

        points: list[float] = [0.0]

        # Clip edges
        for track in self.timeline.tracks:
            for clip in track.clips:
                points.append(clip.timeline_start)
                points.append(clip.timeline_end)

        # Markers
        for marker in self.timeline.markers:
            points.append(marker.time)

        return sorted(set(points))

    # ==========================================================
    # Generic Snap
    # ==========================================================

    def snap(
        self,
        position: float,
    ) -> float:
        """
        Snap a timeline position.
        """

        best = position
        best_distance = self.threshold

        for point in self.snap_points():
            distance = abs(point - position)

            if distance <= best_distance:
                best = point
                best_distance = distance

        return best

    # ==========================================================
    # Clip Start
    # ==========================================================

    def snap_clip_start(
        self,
        clip: Clip,
        new_start: float,
    ) -> float:
        """
        Snap clip start.
        """

        return self.snap(new_start)

    # ==========================================================
    # Clip End
    # ==========================================================

    def snap_clip_end(
        self,
        clip: Clip,
        new_end: float,
    ) -> float:
        """
        Snap clip end.

        Returns the corrected end time.
        """

        snapped = self.snap(new_end)

        return snapped

    # ==========================================================
    # Playhead
    # ==========================================================

    def snap_to_playhead(
        self,
        position: float,
        playhead: float,
    ) -> float:
        """
        Snap to playhead if nearby.
        """

        if abs(position - playhead) <= self.threshold:
            return playhead

        return position

    # ==========================================================
    # Closest Point
    # ==========================================================

    def closest_point(
        self,
        position: float,
    ) -> float | None:
        """
        Return nearest snap point.
        """

        points = self.snap_points()

        if not points:
            return None

        return min(
            points,
            key=lambda p: abs(p - position),
        )

    # ==========================================================
    # Enable / Disable
    # ==========================================================

    def set_threshold(
        self,
        threshold: float,
    ) -> None:
        """
        Change snap sensitivity.
        """

        self.threshold = max(0.0, threshold)
