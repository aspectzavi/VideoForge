"""
VideoForge Clip

A Clip represents an editable instance of a MediaAsset on a timeline.

Unlike MediaAsset, which represents the source file, a Clip contains
editing information such as:

- in/out points
- timeline position
- playback speed
- transforms
- opacity
- mute
- effects
"""

from __future__ import annotations

import uuid
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, computed_field

from videoforge.media.asset import MediaAsset
from videoforge.media.effect import Effect
from videoforge.media.transition import Transition

# ==========================================================
# Transform
# ==========================================================


class ClipTransform(BaseModel):
    """
    Spatial transform.
    """

    x: float = 0.0

    y: float = 0.0

    scale_x: float = 1.0

    scale_y: float = 1.0

    rotation: float = 0.0


# ==========================================================
# Crop
# ==========================================================


class ClipCrop(BaseModel):
    left: int = 0

    top: int = 0

    right: int = 0

    bottom: int = 0


# ==========================================================
# Clip
# ==========================================================


class Clip(BaseModel):
    """
    Editable media clip.
    """

    model_config = ConfigDict(
        arbitrary_types_allowed=True,
    )

    # ---------------------------------------------------------
    # Identity
    # ---------------------------------------------------------

    id: str = Field(
        default_factory=lambda: uuid.uuid4().hex,
    )

    name: str | None = None

    color: str = "#4A90E2"

    locked: bool = False

    selected: bool = False

    asset: MediaAsset

    # ---------------------------------------------------------
    # Source Range
    # ---------------------------------------------------------

    source_start: float = 0.0

    source_end: float | None = None

    # ---------------------------------------------------------
    # Timeline
    # ---------------------------------------------------------

    timeline_start: float = 0.0

    track_index: int = 0

    layer: int = 0

    # ---------------------------------------------------------
    # Playback
    # ---------------------------------------------------------

    speed: float = 1.0

    reverse: bool = False

    muted: bool = False

    volume: float = 1.0

    balance: float = 0.0

    fade_in: float = 0.0

    fade_out: float = 0.0

    opacity: float = 1.0

    blend_mode: str = "normal"

    enabled: bool = True

    transition_in: Transition | None = None

    transition_out: Transition | None = None

    stabilized: bool = False

    proxy_path: str | None = None

    cache_key: str | None = None

    # ---------------------------------------------------------
    # Time Remapping
    # ---------------------------------------------------------

    time_remap: list[tuple[float, float]] = Field(
        default_factory=list,
    )

    # ---------------------------------------------------------
    # Effects
    # ---------------------------------------------------------

    effects: list[Effect] = Field(
        default_factory=list,
    )

    # ---------------------------------------------------------
    # Transform
    # ---------------------------------------------------------

    transform: ClipTransform = Field(
        default_factory=ClipTransform,
    )

    crop: ClipCrop = Field(
        default_factory=ClipCrop,
    )

    # ---------------------------------------------------------
    # Metadata
    # ---------------------------------------------------------

    tags: list[str] = Field(
        default_factory=list,
    )

    metadata: dict[str, Any] = Field(
        default_factory=dict,
    )

    # ==========================================================
    # Computed
    # ==========================================================

    @computed_field
    @property
    def source_duration(self) -> float:

        end = self.source_end if self.source_end is not None else self.asset.duration

        return max(
            0.0,
            end - self.source_start,
        )

    @computed_field
    @property
    def duration(self) -> float:

        if self.speed <= 0:
            return 0.0

        return self.source_duration / self.speed

    @computed_field
    @property
    def timeline_end(self) -> float:

        return self.timeline_start + self.duration

    @computed_field
    @property
    def width(self) -> int:

        return self.asset.width

    @computed_field
    @property
    def height(self) -> int:

        return self.asset.height

    @computed_field
    @property
    def resolution(self) -> str:

        return self.asset.resolution

    @computed_field
    @property
    def is_video(self) -> bool:

        return self.asset.asset_type == "video"

    @computed_field
    @property
    def is_audio(self) -> bool:

        return self.asset.asset_type == "audio"

    @computed_field
    @property
    def is_image(self) -> bool:

        return self.asset.asset_type == "image"

    @computed_field
    @property
    def has_effects(self) -> bool:
        return bool(self.effects)

    @computed_field
    @property
    def has_transition(self) -> bool:
        return self.transition_in is not None or self.transition_out is not None

    @computed_field
    @property
    def has_proxy(self) -> bool:
        return self.proxy_path is not None

    @computed_field
    @property
    def is_enabled(self) -> bool:
        return self.enabled and not self.locked

    @computed_field
    @property
    def center_x(self) -> float:
        return self.transform.x + self.width / 2

    @computed_field
    @property
    def center_y(self) -> float:
        return self.transform.y + self.height / 2

    @computed_field
    @property
    def aspect_ratio(self) -> float:
        return self.asset.aspect_ratio

    # ==========================================================
    # Editing
    # ==========================================================

    def trim(
        self,
        start: float,
        end: float,
    ) -> None:

        if end < start:
            raise ValueError("end must be >= start")

        self.source_start = start
        self.source_end = end

    def move(
        self,
        position: float,
    ) -> None:

        self.timeline_start = max(
            0.0,
            position,
        )

    def offset(
        self,
        seconds: float,
    ) -> None:

        self.timeline_start = max(
            0.0,
            self.timeline_start + seconds,
        )

    def resize(
        self,
        duration: float,
    ) -> None:

        if duration <= 0:
            raise ValueError("duration must be positive")

        self.source_end = self.source_start + (duration * self.speed)

    def set_speed(
        self,
        speed: float,
    ) -> None:

        if speed <= 0:
            raise ValueError("speed must be > 0")

        self.speed = speed

    def mute(self) -> None:

        self.muted = True

    def unmute(self) -> None:

        self.muted = False

    def disable(self) -> None:

        self.enabled = False

    def enable(self) -> None:

        self.enabled = True

    def add_effect(
        self,
        effect: Effect,
    ) -> None:
        self.effects.append(effect)

    def remove_effect(
        self,
        effect: Effect,
    ) -> None:
        if effect in self.effects:
            self.effects.remove(effect)

    def clear_effects(self) -> None:
        self.effects.clear()

    def lock(self) -> None:
        self.locked = True

    def unlock(self) -> None:
        self.locked = False

    def select(self) -> None:
        self.selected = True

    def deselect(self) -> None:
        self.selected = False

    def set_volume(
        self,
        volume: float,
    ) -> None:
        self.volume = min(
            2.0,
            max(0.0, volume),
        )

    def duplicate(
        self,
        offset: float = 1.0,
    ) -> Clip:

        clip = self.clone()

        clip.timeline_start += offset

        return clip

    def split(
        self,
        timeline_position: float,
    ) -> tuple[Clip, Clip]:
        """
        Split this clip into two clips at a timeline position.

        Returns
        -------
        tuple[Clip, Clip]
            (left_clip, right_clip)
        """

        if not (self.timeline_start < timeline_position < self.timeline_end):
            raise ValueError("Split position must lie within the clip.")

        split_offset = timeline_position - self.timeline_start
        source_split = self.source_start + (split_offset * self.speed)

        left = self.clone()
        right = self.clone()

        # Left clip keeps the beginning.
        left.source_end = source_split

        # Right clip starts at the split point.
        right.source_start = source_split
        right.timeline_start = timeline_position

        # Prevent transitions crossing the split.
        left.transition_out = None
        right.transition_in = None

        return left, right

    # ==========================================================
    # Helpers
    # ==========================================================

    def clone(self) -> Clip:

        clone = self.model_copy(
            deep=True,
        )

        clone.id = uuid.uuid4().hex

        return clone

    def __str__(self) -> str:

        return self.name or self.asset.filename

    def __repr__(self) -> str:
        return (
            f"Clip(\n"
            f"  id='{self.id[:8]}',\n"
            f"  asset='{self.asset.filename}',\n"
            f"  type='{self.asset.asset_type}',\n"
            f"  start={self.timeline_start:.2f},\n"
            f"  end={self.timeline_end:.2f},\n"
            f"  duration={self.duration:.2f},\n"
            f"  speed={self.speed}x,\n"
            f"  track={self.track_index},\n"
            f"  effects={len(self.effects)}\n"
            f")"
        )
