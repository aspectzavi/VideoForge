"""
FFmpeg media probing utilities.

Provides a typed wrapper around ffprobe.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field, computed_field

from videoforge.engine.exceptions import FFmpegExecutionError
from videoforge.engine.logger import logger
from videoforge.ffmpeg.binaries import BINARIES

# ---------------------------------------------------------------------
# Stream Models
# ---------------------------------------------------------------------


class VideoStream(BaseModel):
    index: int

    codec: str | None = None

    width: int | None = None

    height: int | None = None

    pix_fmt: str | None = None

    profile: str | None = None

    bit_rate: int | None = None

    frame_rate: str | None = None

    duration: float | None = None


class AudioStream(BaseModel):
    index: int

    codec: str | None = None

    channels: int | None = None

    sample_rate: int | None = None

    bit_rate: int | None = None

    language: str | None = None

    duration: float | None = None


class SubtitleStream(BaseModel):
    index: int

    codec: str | None = None

    language: str | None = None


# ---------------------------------------------------------------------
# Format Model
# ---------------------------------------------------------------------


class MediaFormat(BaseModel):
    filename: str

    format_name: str | None = None

    format_long_name: str | None = None

    duration: float | None = None

    size: int | None = None

    bit_rate: int | None = None


# ---------------------------------------------------------------------
# Final Metadata Model
# ---------------------------------------------------------------------


class MediaInfo(BaseModel):
    format: MediaFormat

    videos: list[VideoStream] = Field(default_factory=list)

    audios: list[AudioStream] = Field(default_factory=list)

    subtitles: list[SubtitleStream] = Field(default_factory=list)

    @property
    def video(self) -> VideoStream | None:
        return self.videos[0] if self.videos else None

    @property
    def audio(self) -> AudioStream | None:
        return self.audios[0] if self.audios else None

    @computed_field
    @property
    def width(self) -> int | None:
        return self.video.width if self.video else None

    @computed_field
    @property
    def height(self) -> int | None:
        return self.video.height if self.video else None

    @computed_field
    @property
    def duration(self) -> float | None:
        return self.format.duration

    @computed_field
    @property
    def fps(self) -> float | None:
        if not self.video or not self.video.frame_rate:
            return None

        num, den = self.video.frame_rate.split("/")
        return round(float(num) / float(den), 3)

    @computed_field
    @property
    def aspect_ratio(self) -> float | None:
        if not self.width or not self.height:
            return None

        return round(self.width / self.height, 3)

    @computed_field
    @property
    def resolution(self) -> str | None:
        if not self.width or not self.height:
            return None

        return f"{self.width}x{self.height}"

    @computed_field
    @property
    def is_vertical(self) -> bool:
        if not self.width or not self.height:
            return False

        return self.height > self.width

    @computed_field
    @property
    def has_audio(self) -> bool:
        return len(self.audios) > 0

    @computed_field
    @property
    def has_subtitles(self) -> bool:
        return len(self.subtitles) > 0


# ---------------------------------------------------------------------
# Probe
# ---------------------------------------------------------------------


class MediaProbe:
    def probe(self, media: str | Path) -> MediaInfo:

        media = Path(media)

        logger.info(f"Probing {media}")

        command = [
            str(BINARIES.ffprobe),
            "-v",
            "quiet",
            "-print_format",
            "json",
            "-show_format",
            "-show_streams",
            str(media),
        ]

        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                check=True,
            )

        except subprocess.CalledProcessError as exc:
            logger.error(exc.stderr)

            raise FFmpegExecutionError(exc.stderr) from exc

        data: dict[str, Any] = json.loads(result.stdout)

        return self._parse(data)

    # -------------------------------------------------------------

    def _parse(self, data: dict[str, Any]) -> MediaInfo:

        fmt = data["format"]

        media_format = MediaFormat(
            filename=fmt["filename"],
            format_name=fmt.get("format_name"),
            format_long_name=fmt.get("format_long_name"),
            duration=float(fmt["duration"]) if fmt.get("duration") else None,
            size=int(fmt["size"]) if fmt.get("size") else None,
            bit_rate=int(fmt["bit_rate"]) if fmt.get("bit_rate") else None,
        )

        videos: list[VideoStream] = []

        audios: list[AudioStream] = []

        subtitles: list[SubtitleStream] = []

        for stream in data["streams"]:
            stream_type = stream["codec_type"]

            if stream_type == "video":
                videos.append(
                    VideoStream(
                        index=stream["index"],
                        codec=stream.get("codec_name"),
                        width=stream.get("width"),
                        height=stream.get("height"),
                        pix_fmt=stream.get("pix_fmt"),
                        profile=stream.get("profile"),
                        bit_rate=int(stream["bit_rate"])
                        if stream.get("bit_rate")
                        else None,
                        frame_rate=stream.get("r_frame_rate"),
                        duration=float(stream["duration"])
                        if stream.get("duration")
                        else None,
                    )
                )

            elif stream_type == "audio":
                audios.append(
                    AudioStream(
                        index=stream["index"],
                        codec=stream.get("codec_name"),
                        channels=stream.get("channels"),
                        sample_rate=int(stream["sample_rate"])
                        if stream.get("sample_rate")
                        else None,
                        bit_rate=int(stream["bit_rate"])
                        if stream.get("bit_rate")
                        else None,
                        language=stream.get("tags", {}).get("language"),
                        duration=float(stream["duration"])
                        if stream.get("duration")
                        else None,
                    )
                )

            elif stream_type == "subtitle":
                subtitles.append(
                    SubtitleStream(
                        index=stream["index"],
                        codec=stream.get("codec_name"),
                        language=stream.get("tags", {}).get("language"),
                    )
                )

        return MediaInfo(
            format=media_format,
            videos=videos,
            audios=audios,
            subtitles=subtitles,
        )


probe = MediaProbe()
