"""
VideoForge Effect Models

Represents timeline effects that can later be translated into
FFmpeg filters or filter graphs.

These classes are intentionally engine-agnostic.
"""

from __future__ import annotations

from enum import StrEnum
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field, computed_field

# ==========================================================
# Effect Type
# ==========================================================


class EffectType(StrEnum):
    VIDEO = "video"
    AUDIO = "audio"
    COLOR = "color"
    SPEED = "speed"
    BLUR = "blur"
    SHARPEN = "sharpen"
    CHROMA_KEY = "chroma_key"
    STABILIZATION = "stabilization"
    CUSTOM = "custom"


# ==========================================================
# Base Effect
# ==========================================================


class Effect(BaseModel):
    """
    Generic timeline effect.

    Effects are attached to Clips or Tracks.
    """

    model_config = ConfigDict(
        arbitrary_types_allowed=True,
    )

    id: str = Field(default_factory=lambda: uuid4().hex)
    name: str
    type: EffectType = EffectType.CUSTOM
    enabled: bool = True

    # Optional time range (None end means full clip duration)
    start: float = 0.0
    end: float | None = None

    parameters: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)

    # -----------------------------------------------------
    # Computed
    # -----------------------------------------------------

    @computed_field
    @property
    def duration(self) -> float | None:
        if self.end is None:
            return None
        return max(0.0, self.end - self.start)

    @computed_field
    @property
    def is_enabled(self) -> bool:
        return self.enabled

    # -----------------------------------------------------
    # Parameter helpers
    # -----------------------------------------------------

    def set(self, key: str, value: Any) -> None:
        """Set a parameter value."""
        self.parameters[key] = value

    def get(self, key: str, default: Any = None) -> Any:
        """Get a parameter value."""
        return self.parameters.get(key, default)

    def has(self, key: str) -> bool:
        return key in self.parameters

    def remove(self, key: str) -> None:
        self.parameters.pop(key, None)

    def clear_parameters(self) -> None:
        self.parameters.clear()

    # -----------------------------------------------------
    # State
    # -----------------------------------------------------

    def enable(self) -> None:
        self.enabled = True

    def disable(self) -> None:
        self.enabled = False

    def toggle(self) -> None:
        self.enabled = not self.enabled

    # -----------------------------------------------------
    # Timing
    # -----------------------------------------------------

    def set_range(self, start: float, end: float | None = None) -> None:
        self.start = start
        self.end = end

    def clear_range(self) -> None:
        self.start = 0.0
        self.end = None

    # -----------------------------------------------------
    # Cloning & Serialization
    # -----------------------------------------------------

    def clone(self) -> Effect:
        """Deep-copy the effect and assign a new unique ID."""
        clone = self.model_copy(deep=True)
        clone.id = uuid4().hex
        return clone

    def to_dict(self) -> dict[str, Any]:
        return self.model_dump()

    # -----------------------------------------------------
    # FFmpeg
    # -----------------------------------------------------

    def ffmpeg_filter(self) -> str:
        """
        Override in subclasses.

        Returns
        -------
        FFmpeg filter expression.
        """
        raise NotImplementedError(
            f"{self.__class__.__name__} does not implement ffmpeg_filter()."
        )

    # -----------------------------------------------------
    # Representation
    # -----------------------------------------------------

    def __str__(self) -> str:
        return self.name

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}("
            f"name='{self.name}', "
            f"type={self.type.value}, "
            f"enabled={self.enabled})"
        )


# ==========================================================
# Blur
# ==========================================================


class BlurEffect(Effect):
    strength: int = 20
    type: EffectType = EffectType.BLUR
    name: str = "Blur"

    def ffmpeg_filter(self) -> str:
        return f"boxblur={self.strength}"


# ==========================================================
# Sharpen
# ==========================================================


class SharpenEffect(Effect):
    amount: float = 1.0
    type: EffectType = EffectType.SHARPEN
    name: str = "Sharpen"

    def ffmpeg_filter(self) -> str:
        return f"unsharp=5:5:{self.amount}:5:5:0"


# ==========================================================
# Color (Brightness / Contrast / Saturation / Gamma)
# ==========================================================


class ColorEffect(Effect):
    brightness: float = 0.0
    contrast: float = 1.0
    saturation: float = 1.0
    gamma: float = 1.0
    type: EffectType = EffectType.COLOR
    name: str = "Color"

    def ffmpeg_filter(self) -> str:
        return (
            "eq="
            f"brightness={self.brightness}:"
            f"contrast={self.contrast}:"
            f"saturation={self.saturation}:"
            f"gamma={self.gamma}"
        )


# ==========================================================
# Speed
# ==========================================================


class SpeedEffect(Effect):
    multiplier: float = 1.0
    type: EffectType = EffectType.SPEED
    name: str = "Speed"

    def ffmpeg_filter(self) -> str:
        # Avoid division by zero
        factor = 1.0 / self.multiplier if self.multiplier != 0 else 1.0
        return f"setpts={factor}*PTS"


# ==========================================================
# Volume
# ==========================================================


class VolumeEffect(Effect):
    volume: float = 1.0
    type: EffectType = EffectType.AUDIO
    name: str = "Volume"

    def ffmpeg_filter(self) -> str:
        return f"volume={self.volume}"


# ==========================================================
# Chroma Key
# ==========================================================


class ChromaKeyEffect(Effect):
    color: str = "0x00FF00"  # green by default
    similarity: float = 0.1
    blend: float = 0.0
    type: EffectType = EffectType.CHROMA_KEY
    name: str = "Chroma Key"

    def ffmpeg_filter(self) -> str:
        return f"chromakey=color={self.color}:similarity={self.similarity}:blend={self.blend}"


# ==========================================================
# Custom
# ==========================================================


class CustomEffect(Effect):
    filter_expression: str
    type: EffectType = EffectType.CUSTOM
    name: str = "Custom"

    def ffmpeg_filter(self) -> str:
        return self.filter_expression
