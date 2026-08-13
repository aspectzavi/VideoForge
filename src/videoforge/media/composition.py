"""
VideoForge Composition

A Composition is a self-contained sequence of tracks that can be nested inside
other timelines or rendered independently.

Examples
--------
- Main timeline
- Intro animation
- Lower-third template
- Picture-in-picture sequence
- Motion graphics composition
"""

from __future__ import annotations

from typing import Any
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field, computed_field

from videoforge.media.clip import Clip
from videoforge.media.track import Track


class Composition(BaseModel):
    """
    A reusable renderable composition.
    """

    model_config = ConfigDict(
        arbitrary_types_allowed=True,
    )

    # ---------------------------------------------------------
    # Identity
    # ---------------------------------------------------------

    id: str = Field(
        default_factory=lambda: uuid4().hex,
    )

    name: str = "Composition"

    # ---------------------------------------------------------
    # Timeline Contents
    # ---------------------------------------------------------

    tracks: list[Track] = Field(
        default_factory=list,
    )

    # ---------------------------------------------------------
    # Output Settings
    # ---------------------------------------------------------

    width: int = 1920

    height: int = 1080

    fps: float = 30.0

    background_color: str = "#000000"

    # ---------------------------------------------------------
    # Metadata
    # ---------------------------------------------------------

    metadata: dict[str, Any] = Field(
        default_factory=dict,
    )

    # =========================================================
    # Computed
    # =========================================================

    @computed_field
    @property
    def duration(self) -> float:

        if not self.tracks:
            return 0.0

        return max(track.duration for track in self.tracks)

    @computed_field
    @property
    def track_count(self) -> int:
        return len(self.tracks)

    @computed_field
    @property
    def clip_count(self) -> int:
        return sum(track.clip_count for track in self.tracks)

    @computed_field
    @property
    def resolution(self) -> str:
        return f"{self.width}x{self.height}"

    @computed_field
    @property
    def aspect_ratio(self) -> float:
        return round(
            self.width / self.height,
            3,
        )

    @computed_field
    @property
    def is_vertical(self) -> bool:
        return self.height > self.width

    # =========================================================
    # Track Operations
    # =========================================================

    def add_track(
        self,
        track: Track,
    ) -> Track:

        self.tracks.append(track)

        return track

    def remove_track(
        self,
        track: Track,
    ) -> None:

        if track in self.tracks:
            self.tracks.remove(track)

    # =========================================================
    # Clip Operations
    # =========================================================

    def add_clip(
        self,
        clip: Clip,
        track_index: int = 0,
    ) -> Clip:

        if track_index >= len(self.tracks):
            raise IndexError("Track index out of range.")

        self.tracks[track_index].add_clip(clip)

        return clip

    def remove_clip(
        self,
        clip: Clip,
    ) -> None:

        for track in self.tracks:
            if clip in track.clips:
                track.remove_clip(clip)
                return

    def clips_at(
        self,
        time: float,
    ) -> list[Clip]:

        clips: list[Clip] = []

        for track in self.tracks:
            if not track.enabled:
                continue

            for clip in track.clips:
                if clip.enabled and clip.timeline_start <= time < clip.timeline_end:
                    clips.append(clip)

        return clips

    def flatten(self) -> list[Clip]:

        clips: list[Clip] = []

        for track in self.tracks:
            clips.extend(track.clips)

        clips.sort(
            key=lambda clip: (
                clip.timeline_start,
                clip.track_index,
            )
        )

        return clips

    # =========================================================
    # Utilities
    # =========================================================

    def clear(self) -> None:

        self.tracks.clear()

    def duplicate(self) -> Composition:

        duplicate = self.model_copy(
            deep=True,
        )

        duplicate.id = uuid4().hex

        return duplicate

    def summary(self) -> dict[str, Any]:

        return {
            "name": self.name,
            "resolution": self.resolution,
            "fps": self.fps,
            "duration": self.duration,
            "tracks": self.track_count,
            "clips": self.clip_count,
            "vertical": self.is_vertical,
        }

    def __len__(self) -> int:
        return self.clip_count

    def __str__(self) -> str:
        return self.name

    def __repr__(self) -> str:

        return (
            "Composition("
            f"name='{self.name}', "
            f"tracks={self.track_count}, "
            f"clips={self.clip_count}, "
            f"duration={self.duration:.2f}s)"
        )
