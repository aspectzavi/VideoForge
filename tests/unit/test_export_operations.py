"""
Fast, pytest-based tests for operations/export/*.py.

prepare() in all four operations does real filesystem existence
checks, so tests use tmp_path with a real (fake-content) input file.
No FFmpeg subprocess is ever spawned - build_job() only constructs
FFmpegJob objects.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from videoforge.operations.base import OperationContext
from videoforge.operations.export.gif import GifOperation
from videoforge.operations.export.proxy import ProxyOperation
from videoforge.operations.export.spritesheet import SpritesheetOperation
from videoforge.operations.export.thumbnail import ThumbnailOperation


@pytest.fixture
def context(tmp_path: Path) -> OperationContext:
    input_video = tmp_path / "input.mp4"
    input_video.write_bytes(b"fake video")
    return OperationContext(input_file=input_video)


# ---------------------------------------------------------------------
# ThumbnailOperation
# ---------------------------------------------------------------------


def test_thumbnail_prepare_validates(context: OperationContext, tmp_path: Path) -> None:
    op = ThumbnailOperation(tmp_path / "thumb.jpg", time=5.0)
    op.prepare(context)  # should not raise


def test_thumbnail_prepare_rejects_missing_input(tmp_path: Path) -> None:
    ctx = OperationContext(input_file=tmp_path / "missing.mp4")
    op = ThumbnailOperation(tmp_path / "thumb.jpg")

    with pytest.raises(FileNotFoundError):
        op.prepare(ctx)


def test_thumbnail_prepare_rejects_output_equal_to_input(
    tmp_path: Path,
) -> None:
    input_video = tmp_path / "input.mp4"
    input_video.write_bytes(b"x")
    ctx = OperationContext(input_file=input_video)
    op = ThumbnailOperation(input_video)

    with pytest.raises(ValueError, match="different from the input"):
        op.prepare(ctx)


def test_thumbnail_rejects_negative_time() -> None:
    with pytest.raises(ValueError):
        ThumbnailOperation("thumb.jpg", time=-1.0)


def test_thumbnail_build_job_seeks_and_captures_one_frame(
    context: OperationContext, tmp_path: Path
) -> None:
    output = tmp_path / "thumb.jpg"
    op = ThumbnailOperation(output, time=3.5)

    job = op.build_job(context)

    assert job.output == output
    assert job.start_time == pytest.approx(3.5)
    assert job.extra_args == ["-frames:v", "1"]
    assert job.video_filters == []


def test_thumbnail_build_job_with_dimensions(
    context: OperationContext, tmp_path: Path
) -> None:
    op = ThumbnailOperation(tmp_path / "thumb.jpg", width=320)
    job = op.build_job(context)

    assert job.video_filters == ["scale=320:-1"]


def test_thumbnail_finalize_does_not_touch_input_file(
    context: OperationContext, tmp_path: Path
) -> None:
    output = tmp_path / "thumb.jpg"
    op = ThumbnailOperation(output)
    original_input = context.input_file

    op.finalize(context)

    assert context.data["thumbnail_file"] == output
    assert context.input_file == original_input


# ---------------------------------------------------------------------
# GifOperation
# ---------------------------------------------------------------------


def test_gif_prepare_validates(context: OperationContext, tmp_path: Path) -> None:
    op = GifOperation(tmp_path / "out.gif")
    op.prepare(context)  # should not raise


def test_gif_prepare_rejects_output_equal_to_input(tmp_path: Path) -> None:
    input_video = tmp_path / "input.mp4"
    input_video.write_bytes(b"x")
    ctx = OperationContext(input_file=input_video)
    op = GifOperation(input_video)

    with pytest.raises(ValueError, match="different from the input"):
        op.prepare(ctx)


@pytest.mark.parametrize(
    "kwargs",
    [
        {"start": -1.0},
        {"duration": 0},
        {"duration": -5.0},
        {"fps": 0},
        {"width": 0},
    ],
)
def test_gif_rejects_invalid_parameters(kwargs: dict) -> None:
    with pytest.raises(ValueError):
        GifOperation("out.gif", **kwargs)


def test_gif_build_job(context: OperationContext, tmp_path: Path) -> None:
    output = tmp_path / "out.gif"
    op = GifOperation(output, start=2.0, duration=3.0, fps=15, width=320)

    job = op.build_job(context)

    assert job.output == output
    assert job.start_time == pytest.approx(2.0)
    assert job.duration == pytest.approx(3.0)
    assert job.video_filters == ["fps=15,scale=320:-1:flags=lanczos"]
    assert job.extra_args == ["-loop", "0"]


def test_gif_finalize_does_not_touch_input_file(
    context: OperationContext, tmp_path: Path
) -> None:
    output = tmp_path / "out.gif"
    op = GifOperation(output)
    original_input = context.input_file

    op.finalize(context)

    assert context.data["gif_file"] == output
    assert context.input_file == original_input


# ---------------------------------------------------------------------
# SpritesheetOperation
# ---------------------------------------------------------------------


def test_spritesheet_prepare_validates(
    context: OperationContext, tmp_path: Path
) -> None:
    op = SpritesheetOperation(tmp_path / "sheet.jpg")
    op.prepare(context)  # should not raise


def test_spritesheet_frame_count() -> None:
    op = SpritesheetOperation("sheet.jpg", columns=4, rows=3)
    assert op.frame_count == 12


@pytest.mark.parametrize(
    "kwargs",
    [
        {"columns": 0},
        {"rows": 0},
        {"thumb_width": 0},
        {"interval": 0},
        {"interval": -1.0},
    ],
)
def test_spritesheet_rejects_invalid_parameters(kwargs: dict) -> None:
    with pytest.raises(ValueError):
        SpritesheetOperation("sheet.jpg", **kwargs)


def test_spritesheet_build_job_without_interval(
    context: OperationContext, tmp_path: Path
) -> None:
    output = tmp_path / "sheet.jpg"
    op = SpritesheetOperation(output, columns=5, rows=4, thumb_width=200)

    job = op.build_job(context)

    assert job.output == output
    assert job.video_filters == ["scale=200:-1", "tile=5x4"]
    assert job.extra_args == ["-frames:v", "1"]


def test_spritesheet_build_job_with_interval(
    context: OperationContext, tmp_path: Path
) -> None:
    op = SpritesheetOperation(
        tmp_path / "sheet.jpg", columns=3, rows=3, interval=2.0, thumb_width=100
    )

    job = op.build_job(context)

    assert job.video_filters == ["fps=0.5", "scale=100:-1", "tile=3x3"]


def test_spritesheet_finalize_does_not_touch_input_file(
    context: OperationContext, tmp_path: Path
) -> None:
    output = tmp_path / "sheet.jpg"
    op = SpritesheetOperation(output)
    original_input = context.input_file

    op.finalize(context)

    assert context.data["spritesheet_file"] == output
    assert context.input_file == original_input


# ---------------------------------------------------------------------
# ProxyOperation
# ---------------------------------------------------------------------


def test_proxy_prepare_validates(context: OperationContext, tmp_path: Path) -> None:
    op = ProxyOperation(tmp_path / "proxy.mp4")
    op.prepare(context)  # should not raise


def test_proxy_prepare_rejects_output_equal_to_input(tmp_path: Path) -> None:
    input_video = tmp_path / "input.mp4"
    input_video.write_bytes(b"x")
    ctx = OperationContext(input_file=input_video)
    op = ProxyOperation(input_video)

    with pytest.raises(ValueError, match="different from the input"):
        op.prepare(ctx)


def test_proxy_rejects_nonpositive_width() -> None:
    with pytest.raises(ValueError):
        ProxyOperation("proxy.mp4", width=0)


def test_proxy_build_job_uses_fast_settings_by_default(
    context: OperationContext, tmp_path: Path
) -> None:
    output = tmp_path / "proxy.mp4"
    op = ProxyOperation(output)

    job = op.build_job(context)

    assert job.output == output
    assert job.video_filters == ["scale=960:-2"]
    assert job.video_codec == "libx264"
    assert job.audio_codec == "aac"
    assert job.crf == 28
    assert job.preset == "veryfast"


def test_proxy_build_job_respects_custom_settings(
    context: OperationContext, tmp_path: Path
) -> None:
    output = tmp_path / "proxy.mp4"
    op = ProxyOperation(output, width=640, crf=23, preset="fast")

    job = op.build_job(context)

    assert job.video_filters == ["scale=640:-2"]
    assert job.crf == 23
    assert job.preset == "fast"


def test_proxy_finalize_does_not_touch_input_file(
    context: OperationContext, tmp_path: Path
) -> None:
    output = tmp_path / "proxy.mp4"
    op = ProxyOperation(output)
    original_input = context.input_file

    op.finalize(context)

    assert context.data["proxy_file"] == output
    assert context.input_file == original_input
