"""
Fast, mocked unit tests for VerticalStep.

These tests verify job/filter construction without invoking real
FFmpeg or FFprobe subprocesses. See tests/test_vertical.py for the
slow @pytest.mark.integration test that runs a real conversion.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from videoforge.engine.exceptions import ValidationError
from videoforge.ffmpeg.job import FFmpegJob
from videoforge.operations.base import OperationContext
from videoforge.operations.video.vertical import VerticalOperation, VerticalStep


@pytest.fixture
def fake_media_info() -> MagicMock:
    """A stand-in for MediaInfo, just detailed enough to look real."""

    info = MagicMock()
    info.width = 1920
    info.height = 1080
    info.duration = 12.5
    return info


def _prepared_context(
    step: VerticalStep,
    fake_media_info: MagicMock,
    input_file: Path,
) -> OperationContext:
    """Run prepare() with MediaProbe mocked out, return the context."""

    context = OperationContext(input_file=input_file)

    with patch.object(
        step.probe,
        "probe",
        return_value=fake_media_info,
    ) as mock_probe:
        step.prepare(context)

    mock_probe.assert_called_once_with(input_file)
    assert context.media_info is fake_media_info

    return context


# ---------------------------------------------------------------------
# Construction / validation
# ---------------------------------------------------------------------


def test_vertical_step_default_initialization() -> None:
    step = VerticalStep(output="out.mp4")

    assert step.mode == "blur"
    assert step.output == Path("out.mp4")
    assert step.width == 1080
    assert step.height == 1920
    assert step.video_codec == "libx264"
    assert step.audio_codec == "aac"
    assert step.crf == 20
    assert step.preset == "medium"
    assert step.name == "Vertical Conversion"


def test_vertical_operation_is_alias_for_vertical_step() -> None:
    assert VerticalOperation is VerticalStep


def test_vertical_invalid_mode_raises_validation_error() -> None:
    with pytest.raises(ValidationError):
        VerticalStep(output="out.mp4", mode="stretch")  # type: ignore[arg-type]


# ---------------------------------------------------------------------
# prepare()
# ---------------------------------------------------------------------


def test_vertical_prepare_probes_and_stores_media_info(
    tmp_path: Path,
    fake_media_info: MagicMock,
) -> None:
    step = VerticalStep(output=tmp_path / "out.mp4", mode="crop")
    input_file = tmp_path / "input.mp4"

    context = _prepared_context(step, fake_media_info, input_file)

    assert context.media_info is fake_media_info


# ---------------------------------------------------------------------
# build_job() — crop mode
# ---------------------------------------------------------------------


def test_vertical_crop_mode_builds_scale_and_crop_filter(
    tmp_path: Path,
    fake_media_info: MagicMock,
) -> None:
    output = tmp_path / "out.mp4"
    step = VerticalStep(output=output, mode="crop", width=1080, height=1920)
    context = _prepared_context(step, fake_media_info, tmp_path / "input.mp4")

    job = step.build_job(context)

    assert isinstance(job, FFmpegJob)
    assert job.filter_complex is None
    assert len(job.video_filters) == 1
    assert "scale=-2:1920" in job.video_filters[0]
    assert "crop=1080:1920" in job.video_filters[0]


# ---------------------------------------------------------------------
# build_job() — fit mode
# ---------------------------------------------------------------------


def test_vertical_fit_mode_builds_scale_and_pad_filter(
    tmp_path: Path,
    fake_media_info: MagicMock,
) -> None:
    output = tmp_path / "out.mp4"
    step = VerticalStep(output=output, mode="fit", width=1080, height=1920)
    context = _prepared_context(step, fake_media_info, tmp_path / "input.mp4")

    job = step.build_job(context)

    assert job.filter_complex is None
    assert len(job.video_filters) == 1
    filt = job.video_filters[0]
    assert "scale=1080:1920:force_original_aspect_ratio=decrease" in filt
    assert "pad=1080:1920:(ow-iw)/2:(oh-ih)/2" in filt


# ---------------------------------------------------------------------
# build_job() — blur mode
# ---------------------------------------------------------------------


def test_vertical_blur_mode_builds_filter_complex(
    tmp_path: Path,
    fake_media_info: MagicMock,
) -> None:
    output = tmp_path / "out.mp4"
    step = VerticalStep(output=output, mode="blur", width=1080, height=1920)
    context = _prepared_context(step, fake_media_info, tmp_path / "input.mp4")

    job = step.build_job(context)

    assert job.video_filters == []
    assert job.filter_complex is not None
    assert "boxblur" in job.filter_complex
    assert "overlay=(W-w)/2:(H-h)/2" in job.filter_complex
    assert "scale=1080:1920" in job.filter_complex


# ---------------------------------------------------------------------
# build_job() — shared job settings (output, codecs, CRF, preset)
# ---------------------------------------------------------------------


def test_vertical_build_job_requires_prior_probe(tmp_path: Path) -> None:
    step = VerticalStep(output=tmp_path / "out.mp4", mode="crop")
    context = OperationContext(input_file=tmp_path / "input.mp4")

    with pytest.raises(RuntimeError):
        step.build_job(context)


def test_vertical_build_job_sets_output_path(
    tmp_path: Path,
    fake_media_info: MagicMock,
) -> None:
    output = tmp_path / "clip_vertical.mp4"
    step = VerticalStep(output=output, mode="crop")
    context = _prepared_context(step, fake_media_info, tmp_path / "input.mp4")

    job = step.build_job(context)

    assert job.output == output
    assert context.output_file == output
    assert job.inputs == [context.input_file]
    assert job.overwrite is True


def test_vertical_build_job_sets_codec_options(
    tmp_path: Path,
    fake_media_info: MagicMock,
) -> None:
    step = VerticalStep(
        output=tmp_path / "out.mp4",
        mode="crop",
        video_codec="libx265",
        audio_codec="opus",
    )
    context = _prepared_context(step, fake_media_info, tmp_path / "input.mp4")

    job = step.build_job(context)

    assert job.video_codec == "libx265"
    assert job.audio_codec == "opus"


def test_vertical_build_job_sets_crf_and_preset_via_extra_args(
    tmp_path: Path,
    fake_media_info: MagicMock,
) -> None:
    step = VerticalStep(
        output=tmp_path / "out.mp4",
        mode="crop",
        crf=17,
        preset="slow",
    )
    context = _prepared_context(step, fake_media_info, tmp_path / "input.mp4")

    job = step.build_job(context)

    # NOTE: current implementation threads crf/preset through
    # extra_args rather than FFmpegJob.crf/FFmpegJob.preset — this
    # test documents that actual behavior rather than the ideal one.
    assert "-preset" in job.extra_args
    assert job.extra_args[job.extra_args.index("-preset") + 1] == "slow"
    assert "-crf" in job.extra_args
    assert job.extra_args[job.extra_args.index("-crf") + 1] == "17"
    assert "-movflags" in job.extra_args
    assert "+faststart" in job.extra_args


def test_vertical_build_job_dimensions_reflected_in_filters(
    tmp_path: Path,
    fake_media_info: MagicMock,
) -> None:
    step = VerticalStep(
        output=tmp_path / "out.mp4",
        mode="fit",
        width=720,
        height=1280,
    )
    context = _prepared_context(step, fake_media_info, tmp_path / "input.mp4")

    job = step.build_job(context)

    assert "720" in job.video_filters[0]
    assert "1280" in job.video_filters[0]


# ---------------------------------------------------------------------
# finalize()
# ---------------------------------------------------------------------


def test_vertical_finalize_sets_output_file(tmp_path: Path) -> None:
    output = tmp_path / "out.mp4"
    step = VerticalStep(output=output, mode="crop")
    context = OperationContext(input_file=tmp_path / "input.mp4")

    step.finalize(context)

    assert context.output_file == output
