"""
VideoForge Overlay

Represents any object composited on top of the timeline.

Examples
--------
- Text
- Logo
- Watermark
- Image
- Video overlay
- Shape
- Animated graphic
"""

from __future__ import annotations

import uuid
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, computed_field

from videoforge.media.asset_reference import AssetReference


class OverlayType(StrEnum):
    TEXT = "text"
    IMAGE = "image"
    VIDEO = "video"
    LOGO = "logo"
    WATERMARK = "watermark"
    SHAPE = "shape"
    CUSTOM = "custom"


class TextStyle(BaseModel):
    """Styling options for text-based overlays."""

    font: str = "Arial"
    size: int = 48
    color: str = "#FFFFFF"
    stroke_color: str = "#000000"
    stroke_width: float = 0.0
    bold: bool = False
    italic: bool = False
    alignment: str = "center"  # left | center | right


class Keyframe(BaseModel):
    """A single keyframe for animated properties."""

    time: float
    value: Any


class Overlay(BaseModel):
    """
    Overlay displayed over the rendered frame.
    """

    model_config = ConfigDict(
        arbitrary_types_allowed=True,
    )

    # ---------------------------------------------------------
    # Identity
    # ---------------------------------------------------------

    id: str = Field(default_factory=lambda: uuid.uuid4().hex)
    name: str = "Overlay"
    type: OverlayType = OverlayType.IMAGE
    enabled: bool = True
    locked: bool = False
    selected: bool = False
    z_index: int = 0

    # ---------------------------------------------------------
    # Timing
    # ---------------------------------------------------------

    start: float = 0.0
    end: float = 0.0

    # ---------------------------------------------------------
    # Source
    # ---------------------------------------------------------

    asset_reference: AssetReference | None = None

    # Text-specific fields
    text: str = ""
    text_style: TextStyle = Field(default_factory=TextStyle)

    # ---------------------------------------------------------
    # Placement (normalized coordinates 0.0 – 1.0)
    # ---------------------------------------------------------

    x: float = 0.5
    y: float = 0.5
    width: float | None = None
    height: float | None = None
    rotation: float = 0.0
    opacity: float = Field(default=1.0, ge=0.0, le=1.0)
    scale_x: float = 1.0
    scale_y: float = 1.0
    anchor_x: float = 0.5
    anchor_y: float = 0.5

    # ---------------------------------------------------------
    # Animation
    # ---------------------------------------------------------

    fade_in: float = 0.0
    fade_out: float = 0.0
    animation: str | None = None
    animation_data: dict[str, Any] = Field(default_factory=dict)
    keyframes: dict[str, list[Keyframe]] = Field(default_factory=dict)

    # ---------------------------------------------------------
    # Metadata
    # ---------------------------------------------------------

    tags: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    # =========================================================
    # Computed Properties
    # =========================================================

    @computed_field
    @property
    def duration(self) -> float:
        return max(0.0, self.end - self.start)

    @computed_field
    @property
    def is_visible(self) -> bool:
        return self.enabled and self.duration > 0

    @computed_field
    @property
    def has_asset(self) -> bool:
        return self.asset_reference is not None

    @computed_field
    @property
    def asset_id(self) -> str | None:
        if self.asset_reference is None:
            return None
        return self.asset_reference.asset_id

    @computed_field
    @property
    def is_text(self) -> bool:
        return self.type == OverlayType.TEXT

    # =========================================================
    # Timing Helpers
    # =========================================================

    def contains(self, time: float) -> bool:
        """Return True if the overlay is active at the given timeline time."""
        return self.start <= time < self.end

    def set_duration(self, duration: float) -> None:
        """Set end time relative to the current start."""
        self.end = self.start + max(0.0, duration)

    def set_range(self, start: float, end: float) -> None:
        """Set both start and end times."""
        self.start = start
        self.end = max(start, end)

    # =========================================================
    # Transform Helpers
    # =========================================================

    def move(self, dx: float, dy: float) -> None:
        """Translate the overlay by the given deltas."""
        self.x += dx
        self.y += dy

    def set_position(self, x: float, y: float) -> None:
        self.x = x
        self.y = y

    def resize(self, sx: float, sy: float | None = None) -> None:
        """Multiply current scale by the given factors."""
        if sy is None:
            sy = sx
        self.scale_x *= sx
        self.scale_y *= sy

    def set_scale(self, sx: float, sy: float | None = None) -> None:
        if sy is None:
            sy = sx
        self.scale_x = sx
        self.scale_y = sy

    def set_opacity(self, value: float) -> None:
        self.opacity = max(0.0, min(1.0, value))

    # =========================================================
    # Asset
    # =========================================================

    def set_asset_reference(self, ref: AssetReference | None) -> None:
        self.asset_reference = ref

    def clear_asset(self) -> None:
        self.asset_reference = None

    # =========================================================
    # Text
    # =========================================================

    def set_text(self, text: str) -> None:
        self.text = text

    def set_text_style(self, style: TextStyle) -> None:
        self.text_style = style

    # =========================================================
    # Animation / Keyframes
    # =========================================================

    def add_keyframe(self, property_name: str, time: float, value: Any) -> None:
        if property_name not in self.keyframes:
            self.keyframes[property_name] = []
        self.keyframes[property_name].append(Keyframe(time=time, value=value))
        self.keyframes[property_name].sort(key=lambda k: k.time)

    def clear_keyframes(self, property_name: str | None = None) -> None:
        if property_name is None:
            self.keyframes.clear()
        else:
            self.keyframes.pop(property_name, None)

    # =========================================================
    # State
    # =========================================================

    def enable(self) -> None:
        self.enabled = True

    def disable(self) -> None:
        self.enabled = False

    def toggle(self) -> None:
        self.enabled = not self.enabled

    def lock(self) -> None:
        self.locked = True

    def unlock(self) -> None:
        self.locked = False

    def select(self) -> None:
        self.selected = True

    def deselect(self) -> None:
        self.selected = False

    # =========================================================
    # Tags & Metadata
    # =========================================================

    def add_tag(self, tag: str) -> None:
        if tag not in self.tags:
            self.tags.append(tag)

    def remove_tag(self, tag: str) -> bool:
        if tag in self.tags:
            self.tags.remove(tag)
            return True
        return False

    def clear_tags(self) -> None:
        self.tags.clear()

    def set_metadata(self, key: str, value: Any) -> None:
        self.metadata[key] = value

    def get_metadata(self, key: str, default: Any = None) -> Any:
        return self.metadata.get(key, default)

    def remove_metadata(self, key: str) -> None:
        self.metadata.pop(key, None)

    # =========================================================
    # Utilities
    # =========================================================

    def clone(self) -> Overlay:
        """Deep-copy the overlay and assign a new unique ID."""
        overlay = self.model_copy(deep=True)
        overlay.id = uuid.uuid4().hex
        return overlay

    def to_dict(self) -> dict[str, Any]:
        return self.model_dump()

    # =========================================================
    # Representation
    # =========================================================

    def __str__(self) -> str:
        return self.name

    def __repr__(self) -> str:
        return (
            f"Overlay("
            f"name='{self.name}', "
            f"type={self.type.value}, "
            f"start={self.start:.2f}, "
            f"end={self.end:.2f}"
            f")"
        )
