"""
Validation utilities for FFmpeg jobs.
"""

from __future__ import annotations

from pathlib import Path

from videoforge.engine.exceptions import (
    InvalidCodecError,
    InvalidMediaError,
    ValidationError,
)
from videoforge.ffmpeg.job import FFmpegJob

SUPPORTED_VIDEO_EXTENSIONS = {
    ".mp4",
    ".mov",
    ".mkv",
    ".avi",
    ".webm",
    ".m4v",
    ".flv",
    ".wmv",
}

SUPPORTED_AUDIO_EXTENSIONS = {
    ".mp3",
    ".wav",
    ".aac",
    ".m4a",
    ".flac",
    ".ogg",
}

SUPPORTED_EXTENSIONS = SUPPORTED_VIDEO_EXTENSIONS | SUPPORTED_AUDIO_EXTENSIONS


SUPPORTED_VIDEO_CODECS = {
    "libx264",
    "libx265",
    "libvpx-vp9",
    "libaom-av1",
    "copy",
}

SUPPORTED_AUDIO_CODECS = {
    "aac",
    "libopus",
    "libmp3lame",
    "flac",
    "copy",
}


class JobValidator:
    """
    Validate FFmpeg jobs before execution.
    """

    @staticmethod
    def validate(job: FFmpegJob) -> None:

        JobValidator._validate_inputs(job)

        JobValidator._validate_output(job)

        JobValidator._validate_codecs(job)

    @staticmethod
    def _validate_inputs(job: FFmpegJob) -> None:

        if not job.inputs:
            raise ValidationError("No input files supplied.")

        for media in job.inputs:
            if not media.exists():
                raise ValidationError(f"Input file does not exist: {media}")

            if not media.is_file():
                raise ValidationError(f"Not a file: {media}")

            if media.suffix.lower() not in SUPPORTED_EXTENSIONS:
                raise InvalidMediaError(f"Unsupported input format: {media.suffix}")

    @staticmethod
    def _validate_output(job: FFmpegJob) -> None:

        output = job.output

        if output.suffix.lower() not in SUPPORTED_EXTENSIONS:
            raise ValidationError(f"Unsupported output format: {output.suffix}")

        output.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

    @staticmethod
    def _validate_codecs(job: FFmpegJob) -> None:

        if job.video_codec and job.video_codec not in SUPPORTED_VIDEO_CODECS:
            raise InvalidCodecError(f"Unsupported video codec: {job.video_codec}")

        if job.audio_codec and job.audio_codec not in SUPPORTED_AUDIO_CODECS:
            raise ValidationError(f"Unsupported audio codec: {job.audio_codec}")

        if job.copy_video and job.video_codec:
            raise ValidationError("Cannot specify video_codec when copy_video=True.")

        if job.copy_audio and job.audio_codec:
            raise ValidationError("Cannot specify audio_codec when copy_audio=True.")

    @staticmethod
    def ensure_exists(path: Path) -> None:

        if not path.exists():
            raise ValidationError(f"File not found: {path}")

    @staticmethod
    def ensure_directory(path: Path) -> None:

        if not path.exists():
            path.mkdir(
                parents=True,
                exist_ok=True,
            )

    @staticmethod
    def ensure_extension(
        path: Path,
        allowed: set[str],
    ) -> None:

        if path.suffix.lower() not in allowed:
            raise ValidationError(f"Unsupported extension: {path.suffix}")
