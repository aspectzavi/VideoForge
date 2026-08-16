"""
Fast, pytest-based tests for JobValidator.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from videoforge.engine.exceptions import (
    InvalidCodecError,
    InvalidMediaError,
    ValidationError,
)
from videoforge.ffmpeg.job import FFmpegJob
from videoforge.ffmpeg.validation import JobValidator

SAMPLE_MEDIA = Path("tests/sample_media/input.mp4")


def test_validate_passes_for_a_normal_copy_job(tmp_path: Path) -> None:
    job = FFmpegJob(
        inputs=[SAMPLE_MEDIA],
        output=tmp_path / "out.mp4",
        copy_video=True,
        copy_audio=True,
    )

    JobValidator.validate(job)  # should not raise


def test_validate_rejects_missing_input_file(tmp_path: Path) -> None:
    job = FFmpegJob(
        inputs=[tmp_path / "does_not_exist.mp4"],
        output=tmp_path / "out.mp4",
    )

    with pytest.raises(ValidationError, match="does not exist"):
        JobValidator.validate(job)


def test_validate_rejects_no_inputs(tmp_path: Path) -> None:
    job = FFmpegJob(inputs=[], output=tmp_path / "out.mp4")

    with pytest.raises(ValidationError, match="No input files"):
        JobValidator.validate(job)


def test_validate_rejects_unsupported_input_extension(tmp_path: Path) -> None:
    bogus = tmp_path / "input.xyz"
    bogus.write_bytes(b"x")

    job = FFmpegJob(inputs=[bogus], output=tmp_path / "out.mp4")

    with pytest.raises(InvalidMediaError, match="Unsupported input format"):
        JobValidator.validate(job)


def test_validate_rejects_unsupported_output_extension() -> None:
    job = FFmpegJob(inputs=[SAMPLE_MEDIA], output=Path("out.xyz"))

    with pytest.raises(ValidationError, match="Unsupported output format"):
        JobValidator.validate(job)


@pytest.mark.parametrize(
    "suffix", [".jpg", ".jpeg", ".png", ".bmp", ".webp", ".gif"]
)
def test_validate_accepts_image_and_gif_outputs(tmp_path: Path, suffix: str) -> None:
    """
    Regression test: SUPPORTED_EXTENSIONS previously covered only
    video/audio containers, which meant image and GIF outputs (and
    image inputs, e.g. a watermark PNG) were rejected even though
    FFmpeg handles them fine. Fixed by adding
    SUPPORTED_IMAGE_EXTENSIONS.
    """
    job = FFmpegJob(
        inputs=[SAMPLE_MEDIA],
        output=tmp_path / f"out{suffix}",
        extra_args=["-frames:v", "1"],
    )

    JobValidator.validate(job)  # should not raise


def test_validate_accepts_image_inputs(tmp_path: Path) -> None:
    watermark = tmp_path / "logo.png"
    watermark.write_bytes(b"x")

    job = FFmpegJob(
        inputs=[SAMPLE_MEDIA, watermark],
        output=tmp_path / "out.mp4",
    )

    JobValidator.validate(job)  # should not raise


def test_validate_rejects_unsupported_video_codec() -> None:
    job = FFmpegJob(
        inputs=[SAMPLE_MEDIA], output=Path("out.mp4"), video_codec="mpeg2video"
    )

    with pytest.raises(InvalidCodecError, match="Unsupported video codec"):
        JobValidator.validate(job)


def test_validate_rejects_unsupported_audio_codec() -> None:
    job = FFmpegJob(
        inputs=[SAMPLE_MEDIA], output=Path("out.mp4"), audio_codec="wmav2"
    )

    with pytest.raises(ValidationError, match="Unsupported audio codec"):
        JobValidator.validate(job)


def test_validate_rejects_copy_video_with_explicit_codec() -> None:
    job = FFmpegJob(
        inputs=[SAMPLE_MEDIA],
        output=Path("out.mp4"),
        copy_video=True,
        video_codec="libx264",
    )

    with pytest.raises(ValidationError, match="Cannot specify video_codec"):
        JobValidator.validate(job)


def test_validate_rejects_copy_audio_with_explicit_codec() -> None:
    job = FFmpegJob(
        inputs=[SAMPLE_MEDIA],
        output=Path("out.mp4"),
        copy_audio=True,
        audio_codec="aac",
    )

    with pytest.raises(ValidationError, match="Cannot specify audio_codec"):
        JobValidator.validate(job)
