"""
Represents a single FFmpeg operation.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field


class FFmpegJob(BaseModel):
    """
    A declarative description of an FFmpeg job.

    This class is intentionally high-level. The command builder is
    responsible for translating these fields into FFmpeg CLI arguments.
    """

    # ==========================================================
    # Files
    # ==========================================================

    inputs: list[Path]
    output: Path

    # ==========================================================
    # General
    # ==========================================================

    overwrite: bool = True

    working_directory: Path | None = None

    # ==========================================================
    # Codecs
    # ==========================================================

    video_codec: str | None = None
    audio_codec: str | None = None

    copy_video: bool = False
    copy_audio: bool = False

    # ==========================================================
    # Encoding
    # ==========================================================

    preset: str | None = None
    crf: int | None = None

    video_bitrate: str | None = None
    audio_bitrate: str | None = None

    pixel_format: str | None = None

    profile: str | None = None
    level: str | None = None

    tune: str | None = None

    # ==========================================================
    # Resolution
    # ==========================================================

    width: int | None = None
    height: int | None = None

    keep_aspect_ratio: bool = True

    # ==========================================================
    # Timing
    # ==========================================================

    start_time: float | None = None

    duration: float | None = None

    end_time: float | None = None

    frame_rate: float | None = None

    # ==========================================================
    # Audio
    # ==========================================================

    sample_rate: int | None = None

    channels: int | None = None

    volume: float | None = None

    # ==========================================================
    # Filters
    # ==========================================================

    video_filters: list[str] = Field(default_factory=list)

    audio_filters: list[str] = Field(default_factory=list)

    filter_complex: str | None = None

    # ==========================================================
    # Stream Mapping
    # ==========================================================

    map_streams: list[str] = Field(default_factory=list)

    # ==========================================================
    # Metadata
    # ==========================================================

    metadata: dict[str, str] = Field(default_factory=dict)

    # ==========================================================
    # Hardware Acceleration
    # ==========================================================

    hwaccel: str | None = None

    hwaccel_output_format: str | None = None

    # ==========================================================
    # Performance
    # ==========================================================

    threads: int | None = None

    # ==========================================================
    # Subtitle Support
    # ==========================================================

    subtitle_file: Path | None = None

    subtitle_codec: str | None = None

    burn_subtitles: bool = False

    # ==========================================================
    # Watermark
    # ==========================================================

    watermark: Path | None = None

    watermark_position: str = "top-right"

    watermark_opacity: float = 1.0

    # ==========================================================
    # Thumbnail Extraction
    # ==========================================================

    thumbnail_time: float | None = None

    # ==========================================================
    # Progress
    # ==========================================================

    report_progress: bool = True

    # ==========================================================
    # Advanced
    # ==========================================================

    extra_args: list[str] = Field(default_factory=list)

    environment: dict[str, str] = Field(default_factory=dict)

    user_data: dict[str, Any] = Field(default_factory=dict)

    # ==========================================================
    # Helpers
    # ==========================================================

    @property
    def has_video_filters(self) -> bool:
        return bool(self.video_filters)

    @property
    def has_audio_filters(self) -> bool:
        return bool(self.audio_filters)

    @property
    def has_complex_filter(self) -> bool:
        return self.filter_complex is not None

    @property
    def is_stream_copy(self) -> bool:
        return self.copy_video and self.copy_audio

    @property
    def is_transcoding(self) -> bool:
        return not self.is_stream_copy
