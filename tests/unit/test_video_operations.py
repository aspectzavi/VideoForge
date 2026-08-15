"""
Fast, mocked unit tests for the simple video operations
(operations/video/*.py, excluding vertical.py which has its own
dedicated test files).

None of these operations override prepare() or need real media
probing, so a plain OperationContext with a fake input file is
sufficient — no FFmpeg/FFprobe involved anywhere in this file.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from videoforge.operations.base import OperationContext
from videoforge.operations.video.blur import BlurOperation
from videoforge.operations.video.colors import ColorOperation
from videoforge.operations.video.crop import CropOperation
from videoforge.operations.video.flip import FlipOperation
from videoforge.operations.video.overlay import OverlayOperation
from videoforge.operations.video.resize import ResizeOperation
from videoforge.operations.video.reverse import ReverseOperation
from videoforge.operations.video.rotate import RotateOperation
from videoforge.operations.video.sharpen import SharpenOperation
from videoforge.operations.video.speed import SpeedOperation
from videoforge.operations.video.stabilize import StabilizeOperation
from videoforge.operations.video.trim import TrimOperation
from videoforge.operations.video.watermark import WatermarkOperation


@pytest.fixture
def context(tmp_path: Path) -> OperationContext:
    return OperationContext(input_file=tmp_path / "input.mp4")


# ---------------------------------------------------------------------
# CropOperation
# ---------------------------------------------------------------------


def test_crop_builds_filter(context: OperationContext) -> None:
    op = CropOperation(width=1280, height=720, x=100, y=50)
    job = op.build_job(context)

    assert job.video_filters == ["crop=1280:720:100:50"]


@pytest.mark.parametrize("width,height", [(0, 100), (-1, 100), (100, 0), (100, -1)])
def test_crop_rejects_nonpositive_dimensions(width: int, height: int) -> None:
    with pytest.raises(ValueError):
        CropOperation(width=width, height=height)


def test_crop_finalize_promotes_output_file(context: OperationContext) -> None:
    op = CropOperation(width=100, height=100)
    context.output_file = Path("some_output.mp4")

    op.finalize(context)

    assert context.input_file == Path("some_output.mp4")


# ---------------------------------------------------------------------
# BlurOperation
# ---------------------------------------------------------------------


def test_blur_builds_filter(context: OperationContext) -> None:
    op = BlurOperation(sigma=10.0)
    job = op.build_job(context)

    assert job.video_filters == ["gblur=sigma=10.0"]


def test_blur_rejects_nonpositive_sigma() -> None:
    with pytest.raises(ValueError):
        BlurOperation(sigma=0)

    with pytest.raises(ValueError):
        BlurOperation(sigma=-1)


# ---------------------------------------------------------------------
# ColorOperation
# ---------------------------------------------------------------------


def test_color_builds_eq_filter(context: OperationContext) -> None:
    op = ColorOperation(brightness=0.1, contrast=1.2, saturation=0.9, gamma=1.0)
    job = op.build_job(context)

    assert job.video_filters == ["eq=brightness=0.1:contrast=1.2:saturation=0.9:gamma=1.0"]


def test_color_defaults_are_neutral(context: OperationContext) -> None:
    op = ColorOperation()
    job = op.build_job(context)

    assert job.video_filters == ["eq=brightness=0.0:contrast=1.0:saturation=1.0:gamma=1.0"]


# ---------------------------------------------------------------------
# FlipOperation
# ---------------------------------------------------------------------


def test_flip_horizontal_only(context: OperationContext) -> None:
    op = FlipOperation(horizontal=True, vertical=False)
    job = op.build_job(context)

    assert job.video_filters == ["hflip"]


def test_flip_vertical_only(context: OperationContext) -> None:
    op = FlipOperation(horizontal=False, vertical=True)
    job = op.build_job(context)

    assert job.video_filters == ["vflip"]


def test_flip_both(context: OperationContext) -> None:
    op = FlipOperation(horizontal=True, vertical=True)
    job = op.build_job(context)

    assert job.video_filters == ["hflip,vflip"]


def test_flip_rejects_neither_direction() -> None:
    with pytest.raises(ValueError):
        FlipOperation(horizontal=False, vertical=False)


# ---------------------------------------------------------------------
# ResizeOperation
# ---------------------------------------------------------------------


def test_resize_with_aspect_ratio_uses_scale_and_pad(context: OperationContext) -> None:
    op = ResizeOperation(1080, 1920, keep_aspect_ratio=True)
    job = op.build_job(context)

    assert job.width == 1080
    assert job.height == 1920
    assert job.keep_aspect_ratio is True
    filt = job.video_filters[0]
    assert "scale=1080:1920:force_original_aspect_ratio=decrease" in filt
    assert "pad=1080:1920:(ow-iw)/2:(oh-ih)/2" in filt


def test_resize_without_aspect_ratio_uses_plain_scale(context: OperationContext) -> None:
    op = ResizeOperation(640, 480, keep_aspect_ratio=False)
    job = op.build_job(context)

    assert job.video_filters == ["scale=640:480"]


@pytest.mark.parametrize("width,height", [(0, 100), (100, 0), (-1, 100)])
def test_resize_rejects_nonpositive_dimensions(width: int, height: int) -> None:
    with pytest.raises(ValueError):
        ResizeOperation(width, height)


# ---------------------------------------------------------------------
# RotateOperation
# ---------------------------------------------------------------------


@pytest.mark.parametrize(
    "angle,expected_filters",
    [
        (90, ["transpose=1"]),
        (180, ["transpose=2,transpose=2"]),
        (270, ["transpose=2"]),
    ],
)
def test_rotate_builds_correct_transpose(
    context: OperationContext, angle: int, expected_filters: list[str]
) -> None:
    op = RotateOperation(angle)
    job = op.build_job(context)

    assert job.video_filters == expected_filters


@pytest.mark.parametrize("angle", [0, 45, 91, 360, -90])
def test_rotate_rejects_unsupported_angles(angle: int) -> None:
    with pytest.raises(ValueError):
        RotateOperation(angle)


# ---------------------------------------------------------------------
# SharpenOperation
# ---------------------------------------------------------------------


def test_sharpen_builds_unsharp_filter(context: OperationContext) -> None:
    op = SharpenOperation(amount=2.0)
    job = op.build_job(context)

    assert job.video_filters == ["unsharp=5:5:2.0:5:5:0.0"]


def test_sharpen_rejects_nonpositive_amount() -> None:
    with pytest.raises(ValueError):
        SharpenOperation(amount=0)


# ---------------------------------------------------------------------
# SpeedOperation
# ---------------------------------------------------------------------


def test_speed_normal_builds_setpts_and_atempo(context: OperationContext) -> None:
    op = SpeedOperation(1.0)
    job = op.build_job(context)

    assert job.video_filters == ["setpts=PTS/1.0"]
    assert job.audio_filters == ["atempo=1"]


def test_speed_double_speed(context: OperationContext) -> None:
    op = SpeedOperation(2.0)
    job = op.build_job(context)

    assert job.video_filters == ["setpts=PTS/2.0"]
    assert job.audio_filters == ["atempo=2"]


def test_speed_beyond_atempo_range_chains_filters(context: OperationContext) -> None:
    # atempo is only valid 0.5-2.0 per filter; speed=5 needs chaining:
    # 5.0 -> /2.0 -> 2.5 (still >2.0) -> /2.0 -> 1.25
    op = SpeedOperation(5.0)
    job = op.build_job(context)

    assert job.video_filters == ["setpts=PTS/5.0"]
    assert job.audio_filters == ["atempo=2.0,atempo=2.0,atempo=1.25"]


def test_speed_rejects_nonpositive() -> None:
    with pytest.raises(ValueError):
        SpeedOperation(0)

    with pytest.raises(ValueError):
        SpeedOperation(-1)


# ---------------------------------------------------------------------
# StabilizeOperation
# ---------------------------------------------------------------------


def test_stabilize_builds_vidstabtransform_filter(context: OperationContext) -> None:
    op = StabilizeOperation(Path("transforms.trf"), smoothing=20, zoom=0.5)
    job = op.build_job(context)

    assert job.video_filters == [
        "vidstabtransform=input=transforms.trf:smoothing=20:zoom=0.5"
    ]


# ---------------------------------------------------------------------
# TrimOperation
# ---------------------------------------------------------------------


def test_trim_builds_start_and_duration(context: OperationContext) -> None:
    op = TrimOperation(5.0, 15.0)
    job = op.build_job(context)

    assert op.duration == pytest.approx(10.0)
    assert job.start_time == pytest.approx(5.0)
    assert job.duration == pytest.approx(10.0)


def test_trim_rejects_negative_start() -> None:
    with pytest.raises(ValueError):
        TrimOperation(-1.0, 5.0)


def test_trim_rejects_end_before_or_equal_start() -> None:
    with pytest.raises(ValueError):
        TrimOperation(5.0, 5.0)

    with pytest.raises(ValueError):
        TrimOperation(5.0, 2.0)


# ---------------------------------------------------------------------
# ReverseOperation
# ---------------------------------------------------------------------


def test_reverse_video_and_audio(context: OperationContext) -> None:
    op = ReverseOperation(video=True, audio=True)
    job = op.build_job(context)

    assert job.video_filters == ["reverse"]
    assert job.audio_filters == ["areverse"]


def test_reverse_video_only(context: OperationContext) -> None:
    op = ReverseOperation(video=True, audio=False)
    job = op.build_job(context)

    assert job.video_filters == ["reverse"]
    assert job.audio_filters == []


def test_reverse_rejects_neither() -> None:
    with pytest.raises(ValueError):
        ReverseOperation(video=False, audio=False)


# ---------------------------------------------------------------------
# OverlayOperation
# ---------------------------------------------------------------------


def test_overlay_builds_filter_complex_with_two_inputs(context: OperationContext) -> None:
    overlay_path = Path("logo.png")
    op = OverlayOperation(overlay_path, x=10, y=20)
    job = op.build_job(context)

    assert job.inputs == [context.input_file, overlay_path]
    assert job.filter_complex == "[0:v][1:v]overlay=10:20"
    assert job.map_streams == ["0:a?"]


# ---------------------------------------------------------------------
# WatermarkOperation
# ---------------------------------------------------------------------


@pytest.mark.parametrize(
    "position,expected",
    [
        ("top-left", "20:20"),
        ("top-right", "W-w-20:20"),
        ("bottom-left", "20:H-h-20"),
        ("bottom-right", "W-w-20:H-h-20"),
        ("center", "(W-w)/2:(H-h)/2"),
    ],
)
def test_watermark_position_mapping(
    context: OperationContext, position: str, expected: str
) -> None:
    op = WatermarkOperation(Path("logo.png"), position=position, opacity=1.0)
    job = op.build_job(context)

    assert job.filter_complex == f"[0:v][1:v]overlay={expected}"


def test_watermark_opacity_below_one_uses_colorchannelmixer(
    context: OperationContext,
) -> None:
    op = WatermarkOperation(Path("logo.png"), position="center", opacity=0.5)
    job = op.build_job(context)

    assert "colorchannelmixer=aa=0.5" in job.filter_complex
    assert "[0:v][wm]overlay=(W-w)/2:(H-h)/2" in job.filter_complex


def test_watermark_rejects_out_of_range_opacity() -> None:
    with pytest.raises(ValueError):
        WatermarkOperation(Path("logo.png"), opacity=1.1)

    with pytest.raises(ValueError):
        WatermarkOperation(Path("logo.png"), opacity=-0.1)


def test_watermark_rejects_unsupported_position(context: OperationContext) -> None:
    op = WatermarkOperation(Path("logo.png"), position="middle-earth")

    with pytest.raises(ValueError, match="Unsupported position"):
        op.build_job(context)
