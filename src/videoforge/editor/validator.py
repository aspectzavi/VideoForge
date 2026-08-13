"""
VideoForge Timeline Validator

Validation helpers for editing operations.

The validator never modifies the timeline.
It only verifies correctness and raises ValueError when
an invalid operation is detected.
"""

from __future__ import annotations

from videoforge.media.clip import Clip
from videoforge.media.timeline import Timeline
from videoforge.media.track import Track


class TimelineValidator:
    """
    Timeline validation service.
    """

    # ==========================================================
    # Generic
    # ==========================================================

    @staticmethod
    def ensure(
        condition: bool,
        message: str,
    ) -> None:
        if not condition:
            raise ValueError(message)

    # ==========================================================
    # Timeline
    # ==========================================================

    def validate(
        self,
        timeline: Timeline,
    ) -> bool:
        """
        Validate an entire timeline.

        Returns
        -------
        bool
            True when validation succeeds.
        """

        self.validate_timeline(timeline)

        for track in timeline.tracks:
            self.validate_track(track)

            for clip in track.clips:
                self.validate_clip(clip)
                self.validate_source_range(clip)
                self.validate_speed(clip.speed)
                self.validate_opacity(clip.opacity)
                self.validate_volume(clip.volume)
                self.validate_no_overlap(track, clip)

        return True

    def validate_timeline(
        self,
        timeline: Timeline,
    ) -> None:

        self.ensure(
            timeline is not None,
            "Timeline cannot be None.",
        )

    def validate_track(
        self,
        track: Track,
    ) -> None:

        self.ensure(
            track is not None,
            "Track cannot be None.",
        )

    def validate_clip(
        self,
        clip: Clip,
    ) -> None:

        self.ensure(
            clip is not None,
            "Clip cannot be None.",
        )

    # ==========================================================
    # Time
    # ==========================================================

    def validate_time(
        self,
        seconds: float,
    ) -> None:

        self.ensure(
            seconds >= 0,
            "Timeline time cannot be negative.",
        )

    def validate_duration(
        self,
        duration: float,
    ) -> None:

        self.ensure(
            duration > 0,
            "Duration must be greater than zero.",
        )

    # ==========================================================
    # Track Membership
    # ==========================================================

    def validate_clip_in_track(
        self,
        clip: Clip,
        track: Track,
    ) -> None:

        self.validate_clip(clip)
        self.validate_track(track)

        self.ensure(
            clip in track.clips,
            "Clip is not contained in track.",
        )

    def validate_track_index(
        self,
        timeline: Timeline,
        index: int,
    ) -> None:

        self.validate_timeline(timeline)

        self.ensure(
            0 <= index < len(timeline.tracks),
            f"Track index {index} is out of range.",
        )

    # ==========================================================
    # Locked Objects
    # ==========================================================

    def validate_track_unlocked(
        self,
        track: Track,
    ) -> None:

        self.ensure(
            not track.locked,
            "Track is locked.",
        )

    def validate_clip_unlocked(
        self,
        clip: Clip,
    ) -> None:

        self.ensure(
            not clip.locked,
            "Clip is locked.",
        )

    # ==========================================================
    # Overlap
    # ==========================================================

    def validate_no_overlap(
        self,
        track: Track,
        clip: Clip,
    ) -> None:

        for other in track.clips:
            if other.id == clip.id:
                continue

            overlap = (
                clip.timeline_start < other.timeline_end
                and clip.timeline_end > other.timeline_start
            )

            self.ensure(
                not overlap,
                f"Clip overlaps '{other.name or other.id[:8]}'.",
            )

    # ==========================================================
    # Source Range
    # ==========================================================

    def validate_source_range(
        self,
        clip: Clip,
    ) -> None:

        end = clip.source_end if clip.source_end is not None else clip.asset.duration

        self.ensure(
            clip.source_start >= 0,
            "Source start cannot be negative.",
        )

        self.ensure(
            end >= clip.source_start,
            "Source end must be after source start.",
        )

    # ==========================================================
    # Playback
    # ==========================================================

    def validate_speed(
        self,
        speed: float,
    ) -> None:

        self.ensure(
            speed > 0,
            "Playback speed must be greater than zero.",
        )

    def validate_opacity(
        self,
        opacity: float,
    ) -> None:

        self.ensure(
            0.0 <= opacity <= 1.0,
            "Opacity must be between 0 and 1.",
        )

    def validate_volume(
        self,
        volume: float,
    ) -> None:

        self.ensure(
            volume >= 0,
            "Volume cannot be negative.",
        )
