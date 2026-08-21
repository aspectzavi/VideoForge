"""
VideoForge Renderer Filters

Object-oriented FFmpeg filter definitions.

Instead of constructing FFmpeg filter strings manually throughout the
codebase, every filter is represented by a Python object that can render
itself into FFmpeg syntax.

Example
-------
ScaleFilter(width=1080, height=1920)

↓

scale=1080:1920
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from pydantic import BaseModel, Field

# ==========================================================
# Base Filter
# ==========================================================


class Filter(BaseModel, ABC):
    """
    Base FFmpeg filter.
    """

    enabled: bool = True

    @abstractmethod
    def to_ffmpeg(self) -> str:
        """
        Convert this filter into FFmpeg syntax.
        """
        raise NotImplementedError

    # ---------------------------------------------

    def __str__(self) -> str:
        return self.to_ffmpeg()


# ==========================================================
# Video Filters
# ==========================================================


class ScaleFilter(Filter):
    width: int

    height: int

    flags: str | None = None

    def to_ffmpeg(self) -> str:

        expression = f"scale={self.width}:{self.height}"

        if self.flags:
            expression += f":flags={self.flags}"

        return expression


# ----------------------------------------------------------


class CropFilter(Filter):
    width: int

    height: int

    x: str | int = "(iw-ow)/2"

    y: str | int = "(ih-oh)/2"

    def to_ffmpeg(self) -> str:

        return f"crop={self.width}:{self.height}:{self.x}:{self.y}"


# ----------------------------------------------------------


class PadFilter(Filter):
    width: int

    height: int

    x: str | int = "(ow-iw)/2"

    y: str | int = "(oh-ih)/2"

    color: str = "black"

    def to_ffmpeg(self) -> str:

        return f"pad={self.width}:{self.height}:{self.x}:{self.y}:{self.color}"


# ----------------------------------------------------------


class BlurFilter(Filter):
    radius: int = 20

    power: int = 5

    def to_ffmpeg(self) -> str:

        return f"boxblur={self.radius}:{self.power}"


# ----------------------------------------------------------


class RotateFilter(Filter):
    angle: float

    fill_color: str = "black"

    def to_ffmpeg(self) -> str:

        return f"rotate={self.angle}:fillcolor={self.fill_color}"


# ----------------------------------------------------------


class FlipFilter(Filter):
    horizontal: bool = False

    vertical: bool = False

    def to_ffmpeg(self) -> str:

        if self.horizontal and self.vertical:
            return "hflip,vflip"

        if self.horizontal:
            return "hflip"

        if self.vertical:
            return "vflip"

        return ""


# ----------------------------------------------------------


class FPSFilter(Filter):
    fps: float

    def to_ffmpeg(self) -> str:

        return f"fps={self.fps}"


# ----------------------------------------------------------


class TrimFilter(Filter):
    start: float | None = None

    end: float | None = None

    duration: float | None = None

    def to_ffmpeg(self) -> str:

        parts: list[str] = []

        if self.start is not None:
            parts.append(f"start={self.start}")

        if self.end is not None:
            parts.append(f"end={self.end}")

        if self.duration is not None:
            parts.append(f"duration={self.duration}")

        return "trim=" + ":".join(parts)


# ----------------------------------------------------------


class SetPTSFilter(Filter):
    expression: str = "PTS-STARTPTS"

    def to_ffmpeg(self) -> str:

        return f"setpts={self.expression}"


# ----------------------------------------------------------


class DrawTextFilter(Filter):
    text: str

    x: str = "(w-text_w)/2"

    y: str = "(h-text_h)/2"

    font_size: int = 48

    font_color: str = "white"

    border_width: int = 0

    border_color: str = "black"

    font_file: str | None = None

    def to_ffmpeg(self) -> str:

        args = [
            f"text='{self.text}'",
            f"x={self.x}",
            f"y={self.y}",
            f"fontsize={self.font_size}",
            f"fontcolor={self.font_color}",
        ]

        if self.border_width:
            args.append(f"borderw={self.border_width}")
            args.append(f"bordercolor={self.border_color}")

        if self.font_file:
            args.append(f"fontfile={self.font_file}")

        return "drawtext=" + ":".join(args)


# ----------------------------------------------------------


class OverlayFilter(Filter):
    x: str = "(W-w)/2"

    y: str = "(H-h)/2"

    shortest: bool = True

    eof_action: str = "repeat"

    def to_ffmpeg(self) -> str:

        expression = f"overlay={self.x}:{self.y}"

        if self.shortest:
            expression += ":shortest=1"

        expression += f":eof_action={self.eof_action}"

        return expression


# ==========================================================
# Audio Filters
# ==========================================================


class VolumeFilter(Filter):
    volume: float = 1.0

    def to_ffmpeg(self) -> str:

        return f"volume={self.volume}"


# ----------------------------------------------------------


class AudioFadeFilter(Filter):
    fade_type: str = "in"

    start: float = 0.0

    duration: float = 1.0

    def to_ffmpeg(self) -> str:

        return f"afade=t={self.fade_type}:st={self.start}:d={self.duration}"


# ----------------------------------------------------------


class AudioTempoFilter(Filter):
    tempo: float = 1.0

    def to_ffmpeg(self) -> str:

        return f"atempo={self.tempo}"


# ==========================================================
# Generic Filter
# ==========================================================


class CustomFilter(Filter):
    """
    Wrap any FFmpeg filter string.
    """

    expression: str

    def to_ffmpeg(self) -> str:

        return self.expression


# ==========================================================
# Filter Chain
# ==========================================================


class FilterChain(BaseModel):
    """
    Represents a comma-separated FFmpeg filter chain.
    """

    filters: list[Filter] = Field(default_factory=list)

    # -----------------------------------------------------

    def add(
        self,
        *filters: Filter,
    ) -> FilterChain:

        self.filters.extend(filters)

        return self

    # -----------------------------------------------------

    def extend(
        self,
        filters: list[Filter],
    ) -> FilterChain:

        self.filters.extend(filters)

        return self

    # -----------------------------------------------------

    def clear(self) -> None:

        self.filters.clear()

    # -----------------------------------------------------

    def to_ffmpeg(self) -> str:

        return ",".join(
            f.to_ffmpeg() for f in self.filters if f.enabled and f.to_ffmpeg()
        )

    # -----------------------------------------------------

    def __str__(self) -> str:

        return self.to_ffmpeg()

    # -----------------------------------------------------

    def __len__(self) -> int:

        return len(self.filters)

    # -----------------------------------------------------

    def __getitem__(
        self,
        index: int,
    ) -> Filter:

        return self.filters[index]


# ==========================================================
# Utility
# ==========================================================


def build_filter_chain(
    *filters: Filter,
) -> str:
    """
    Convenience helper.

    Example
    -------
    build_filter_chain(
        ScaleFilter(width=1080, height=1920),
        CropFilter(width=1080, height=1920),
    )
    """

    return FilterChain(filters=list(filters)).to_ffmpeg()
