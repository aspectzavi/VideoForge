"""
Timeline settings.

Defines the editing and rendering configuration for a timeline.

Unlike TimelineMetadata, these settings directly affect how the timeline
is rendered and exported.
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel

# ==========================================================
# Enums
# ==========================================================


class DurationMode(StrEnum):
    """
    Determines how timeline duration is calculated.
    """

    AUTO = "auto"
    FIXED = "fixed"
    MANUAL = "manual"


class ColorSpace(StrEnum):
    """
    Timeline color space.
    """

    BT601 = "bt601"

    BT709 = "bt709"

    BT2020 = "bt2020"

    SRGB = "srgb"

    DISPLAY_P3 = "display_p3"


class PixelFormat(StrEnum):
    """
    Default output pixel format.
    """

    YUV420P = "yuv420p"

    YUV422P = "yuv422p"

    YUV444P = "yuv444p"

    RGB24 = "rgb24"

    RGBA = "rgba"


class AudioLayout(StrEnum):
    """
    Audio channel layout.
    """

    MONO = "mono"

    STEREO = "stereo"

    SURROUND_5_1 = "5.1"

    SURROUND_7_1 = "7.1"


# ==========================================================
# Timeline Settings
# ==========================================================


class TimelineSettings(BaseModel):
    """
    Rendering and editing settings for a timeline.
    """

    # ------------------------------------------------------
    # Video
    # ------------------------------------------------------

    width: int = 1920

    height: int = 1080

    fps: float = 30.0

    color_space: ColorSpace = ColorSpace.BT709

    pixel_format: PixelFormat = PixelFormat.YUV420P

    background_color: str = "#000000"

    duration_mode: DurationMode = DurationMode.AUTO

    # ------------------------------------------------------
    # Audio
    # ------------------------------------------------------

    sample_rate: int = 48_000

    channels: int = 2

    audio_layout: AudioLayout = AudioLayout.STEREO

    audio_bitrate: int = 192_000

    # ------------------------------------------------------
    # Playback
    # ------------------------------------------------------

    playback_speed: float = 1.0

    proxy_enabled: bool = False

    # ------------------------------------------------------
    # Rendering
    # ------------------------------------------------------

    use_gpu: bool = True

    cache_frames: bool = True

    cache_audio: bool = True

    # ------------------------------------------------------
    # Computed Properties
    # ------------------------------------------------------

    @property
    def resolution(self) -> str:

        return f"{self.width}x{self.height}"

    # ------------------------------------------------------

    @property
    def aspect_ratio(self) -> float:

        return round(
            self.width / self.height,
            4,
        )

    # ------------------------------------------------------

    @property
    def is_vertical(self) -> bool:

        return self.height > self.width

    # ------------------------------------------------------

    @property
    def is_horizontal(self) -> bool:

        return self.width >= self.height

    # ------------------------------------------------------

    @property
    def frame_duration(self) -> float:

        return 1.0 / self.fps

    # ------------------------------------------------------
    # Helpers
    # ------------------------------------------------------

    def set_resolution(
        self,
        width: int,
        height: int,
    ) -> None:

        self.width = width

        self.height = height

    # ------------------------------------------------------

    def set_fps(
        self,
        fps: float,
    ) -> None:

        if fps <= 0:
            raise ValueError("FPS must be greater than zero.")

        self.fps = fps

    # ------------------------------------------------------

    def set_audio(
        self,
        sample_rate: int,
        channels: int,
    ) -> None:

        self.sample_rate = sample_rate

        self.channels = channels

    # ------------------------------------------------------

    def portrait(self) -> None:

        self.width = 1080

        self.height = 1920

    # ------------------------------------------------------

    def landscape(self) -> None:

        self.width = 1920

        self.height = 1080

    # ------------------------------------------------------

    def square(self) -> None:

        self.width = 1080

        self.height = 1080

    # ------------------------------------------------------

    def cinema_4k(self) -> None:

        self.width = 4096

        self.height = 2160

    # ------------------------------------------------------

    def uhd_4k(self) -> None:

        self.width = 3840

        self.height = 2160
