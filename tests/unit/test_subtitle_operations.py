"""
Fast, pytest-based tests for operations/subtitles/*.py.

All prepare() methods here do real filesystem existence checks
(is_file()), so tests create tiny real files under tmp_path rather
than mocking the filesystem. No FFmpeg subprocess is ever spawned —
build_job() only constructs FFmpegJob objects.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from videoforge.operations.base import OperationContext
from videoforge.operations.subtitles.burn_in import BurnInSubtitlesOperation
from videoforge.operations.subtitles.captions import CaptionGenerationOperation
from videoforge.operations.subtitles.convert import ConvertSubtitlesOperation
from videoforge.operations.subtitles.embed import EmbedSubtitlesOperation
from videoforge.operations.subtitles.extract import ExtractOperation


@pytest.fixture
def input_video(tmp_path: Path) -> Path:
    p = tmp_path / "input.mp4"
    p.write_bytes(b"fake video")
    return p


@pytest.fixture
def subtitle_file(tmp_path: Path) -> Path:
    p = tmp_path / "subs.srt"
    p.write_text("1\n00:00:00,000 --> 00:00:01,000\nHello\n")
    return p


@pytest.fixture
def context(input_video: Path) -> OperationContext:
    return OperationContext(input_file=input_video)


# ---------------------------------------------------------------------
# BurnInSubtitlesOperation
# ---------------------------------------------------------------------


def test_burn_in_prepare_validates_files_exist(
    context: OperationContext, subtitle_file: Path, tmp_path: Path
) -> None:
    op = BurnInSubtitlesOperation(subtitle_file, tmp_path / "out.mp4")
    op.prepare(context)  # should not raise

    assert context.data["subtitle_file"] == subtitle_file


def test_burn_in_prepare_rejects_missing_subtitle_file(
    context: OperationContext, tmp_path: Path
) -> None:
    op = BurnInSubtitlesOperation(tmp_path / "missing.srt", tmp_path / "out.mp4")

    with pytest.raises(FileNotFoundError):
        op.prepare(context)


def test_burn_in_prepare_rejects_missing_input_video(
    subtitle_file: Path, tmp_path: Path
) -> None:
    ctx = OperationContext(input_file=tmp_path / "missing.mp4")
    op = BurnInSubtitlesOperation(subtitle_file, tmp_path / "out.mp4")

    with pytest.raises(FileNotFoundError):
        op.prepare(ctx)


def test_burn_in_prepare_rejects_output_equal_to_input(
    input_video: Path, subtitle_file: Path
) -> None:
    ctx = OperationContext(input_file=input_video)
    op = BurnInSubtitlesOperation(subtitle_file, input_video)

    with pytest.raises(ValueError, match="different from the input"):
        op.prepare(ctx)


def test_burn_in_build_job_escapes_subtitle_path(
    context: OperationContext, subtitle_file: Path, tmp_path: Path
) -> None:
    output = tmp_path / "out.mp4"
    op = BurnInSubtitlesOperation(subtitle_file, output)

    job = op.build_job(context)

    assert job.output == output
    assert len(job.video_filters) == 1
    assert job.video_filters[0].startswith("subtitles='")

    # Windows resolved paths always carry a drive-letter colon (e.g.
    # "C:\..."), which the subtitles filter needs escaped or FFmpeg
    # misparses it as a filter-option separator.
    escaped = op._escape_subtitle_path(subtitle_file)
    assert "\\:" in escaped


def test_burn_in_build_job_includes_style_when_given(
    context: OperationContext, subtitle_file: Path, tmp_path: Path
) -> None:
    op = BurnInSubtitlesOperation(
        subtitle_file, tmp_path / "out.mp4", style="FontSize=24"
    )

    job = op.build_job(context)

    assert "force_style='FontSize=24'" in job.video_filters[0]


def test_burn_in_finalize_sets_input_and_output(
    context: OperationContext, subtitle_file: Path, tmp_path: Path
) -> None:
    output = tmp_path / "out.mp4"
    op = BurnInSubtitlesOperation(subtitle_file, output)

    op.finalize(context)

    assert context.output_file == output
    assert context.input_file == output


# ---------------------------------------------------------------------
# CaptionGenerationOperation
# ---------------------------------------------------------------------


def test_caption_generation_defaults() -> None:
    op = CaptionGenerationOperation()
    assert op.format == "srt"
    assert op.language is None


def test_caption_generation_rejects_unsupported_format() -> None:
    with pytest.raises(ValueError, match="format must be one of"):
        CaptionGenerationOperation(format="txt")


def test_caption_generation_normalizes_format_case() -> None:
    op = CaptionGenerationOperation(format="VTT")
    assert op.format == "vtt"


def test_caption_generation_prepare_derives_subtitle_path(
    context: OperationContext,
) -> None:
    op = CaptionGenerationOperation(language="en", format="vtt")
    op.prepare(context)

    assert context.data["subtitle_file"] == context.input_file.with_suffix(".vtt")
    assert context.data["subtitle_language"] == "en"
    assert context.data["subtitle_format"] == "vtt"


def test_caption_generation_build_job_returns_none(
    context: OperationContext,
) -> None:
    op = CaptionGenerationOperation()
    op.prepare(context)

    assert op.build_job(context) is None


def test_caption_generation_subtitle_file_property_always_none(
    context: OperationContext,
) -> None:
    """
    Documents a real quirk: the subtitle_file *property* always
    returns None, even after prepare() has populated
    context.data["subtitle_file"] with the real path. The property
    reads no instance state that prepare() sets — callers must read
    context.data["subtitle_file"] instead of op.subtitle_file.
    """
    op = CaptionGenerationOperation()
    op.prepare(context)

    assert context.data["subtitle_file"] is not None  # the real value
    assert op.subtitle_file is None  # the property, disconnected from it


# ---------------------------------------------------------------------
# ConvertSubtitlesOperation
# ---------------------------------------------------------------------


def test_convert_infers_output_format_from_suffix(tmp_path: Path) -> None:
    op = ConvertSubtitlesOperation(tmp_path / "out.vtt")
    assert op.output_format == "vtt"
    assert op.output_suffix == ".vtt"


def test_convert_rejects_unsupported_output_format(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="output_format must be one of"):
        ConvertSubtitlesOperation(tmp_path / "out.txt")


def test_convert_rejects_unsupported_explicit_input_format(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="input_format must be one of"):
        ConvertSubtitlesOperation(tmp_path / "out.vtt", input_format="txt")


def test_convert_prepare_infers_input_format_from_context(tmp_path: Path) -> None:
    ctx = OperationContext(input_file=tmp_path / "in.srt")
    op = ConvertSubtitlesOperation(tmp_path / "out.vtt")

    op.prepare(ctx)

    assert op.input_format == "srt"
    assert ctx.data["subtitle_input_format"] == "srt"
    assert ctx.data["subtitle_output_format"] == "vtt"


def test_convert_prepare_raises_when_input_format_undeterminable(
    tmp_path: Path,
) -> None:
    ctx = OperationContext(input_file=tmp_path / "in.unknownext")
    op = ConvertSubtitlesOperation(tmp_path / "out.vtt")

    with pytest.raises(ValueError, match="Could not determine"):
        op.prepare(ctx)


def test_convert_prepare_rejects_identical_formats(tmp_path: Path) -> None:
    ctx = OperationContext(input_file=tmp_path / "in.srt")
    op = ConvertSubtitlesOperation(tmp_path / "out.srt")

    with pytest.raises(ValueError, match="identical"):
        op.prepare(ctx)


def test_convert_build_job_maps_first_stream(tmp_path: Path) -> None:
    ctx = OperationContext(input_file=tmp_path / "in.srt")
    output = tmp_path / "out.vtt"
    op = ConvertSubtitlesOperation(output)
    op.prepare(ctx)

    job = op.build_job(ctx)

    assert job.output == output
    assert job.map_streams == ["0:0"]


def test_convert_finalize_sets_input_and_output(tmp_path: Path) -> None:
    ctx = OperationContext(input_file=tmp_path / "in.srt")
    output = tmp_path / "out.vtt"
    op = ConvertSubtitlesOperation(output)

    op.finalize(ctx)

    assert ctx.output_file == output
    assert ctx.input_file == output


# ---------------------------------------------------------------------
# EmbedSubtitlesOperation
# ---------------------------------------------------------------------


def test_embed_prepare_validates_and_normalizes(
    context: OperationContext, subtitle_file: Path, tmp_path: Path
) -> None:
    op = EmbedSubtitlesOperation(
        subtitle_file,
        tmp_path / "out.mkv",
        language="  EN  ",
        title="  English  ",
    )

    op.prepare(context)

    assert op.language == "en"
    assert op.title == "English"
    assert context.data["subtitle_file"] == subtitle_file


def test_embed_prepare_blanks_become_none(
    context: OperationContext, subtitle_file: Path, tmp_path: Path
) -> None:
    op = EmbedSubtitlesOperation(
        subtitle_file, tmp_path / "out.mkv", language="   ", title="   "
    )

    op.prepare(context)

    assert op.language is None
    assert op.title is None


def test_embed_prepare_rejects_missing_subtitle_file(
    context: OperationContext, tmp_path: Path
) -> None:
    op = EmbedSubtitlesOperation(tmp_path / "missing.srt", tmp_path / "out.mkv")

    with pytest.raises(FileNotFoundError):
        op.prepare(context)


def test_embed_prepare_rejects_output_equal_to_input(
    input_video: Path, subtitle_file: Path
) -> None:
    ctx = OperationContext(input_file=input_video)
    op = EmbedSubtitlesOperation(subtitle_file, input_video)

    with pytest.raises(ValueError, match="different from the input"):
        op.prepare(ctx)


def test_embed_build_job_maps_streams_and_copies_codecs(
    context: OperationContext, subtitle_file: Path, tmp_path: Path
) -> None:
    output = tmp_path / "out.mkv"
    op = EmbedSubtitlesOperation(subtitle_file, output, language="en", title="English")
    op.prepare(context)

    job = op.build_job(context)

    assert job.inputs == [context.input_file, subtitle_file]
    assert job.map_streams == ["0:v?", "0:a?", "1:0"]
    assert job.copy_video is True
    assert job.copy_audio is True
    assert job.subtitle_codec == "copy"
    assert job.metadata == {"s:s:0:language": "en", "s:s:0:title": "English"}


def test_embed_build_job_omits_metadata_when_not_given(
    context: OperationContext, subtitle_file: Path, tmp_path: Path
) -> None:
    op = EmbedSubtitlesOperation(subtitle_file, tmp_path / "out.mkv")
    op.prepare(context)

    job = op.build_job(context)

    assert job.metadata == {}


# ---------------------------------------------------------------------
# ExtractOperation
# ---------------------------------------------------------------------


def test_extract_requires_exactly_one_type_selected(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="Exactly one"):
        ExtractOperation(tmp_path / "out.mp3")  # none selected

    with pytest.raises(ValueError, match="Exactly one"):
        ExtractOperation(tmp_path / "out.mp3", audio=True, video=True)


def test_extract_type_property(tmp_path: Path) -> None:
    assert ExtractOperation(tmp_path / "o.mp3", audio=True).extract_type == "audio"
    assert ExtractOperation(tmp_path / "o.mp4", video=True).extract_type == "video"
    assert (
        ExtractOperation(tmp_path / "o.srt", subtitles=True).extract_type
        == "subtitles"
    )


def test_extract_prepare_validates_input_and_output(
    context: OperationContext, tmp_path: Path
) -> None:
    op = ExtractOperation(tmp_path / "out.mp3", audio=True)
    op.prepare(context)  # should not raise

    assert context.data["extract_type"] == "audio"


def test_extract_prepare_rejects_missing_input(tmp_path: Path) -> None:
    ctx = OperationContext(input_file=tmp_path / "missing.mp4")
    op = ExtractOperation(tmp_path / "out.mp3", audio=True)

    with pytest.raises(FileNotFoundError):
        op.prepare(ctx)


def test_extract_prepare_rejects_output_equal_to_input(input_video: Path) -> None:
    ctx = OperationContext(input_file=input_video)
    op = ExtractOperation(input_video, audio=True)

    with pytest.raises(ValueError, match="different from the input"):
        op.prepare(ctx)


def test_extract_build_job_audio(context: OperationContext, tmp_path: Path) -> None:
    output = tmp_path / "out.mp3"
    op = ExtractOperation(output, audio=True)

    job = op.build_job(context)

    assert job.output == output
    assert job.map_streams == ["0:a:0"]
    assert job.copy_audio is True
    assert job.copy_video is False


def test_extract_build_job_video(context: OperationContext, tmp_path: Path) -> None:
    output = tmp_path / "out.mp4"
    op = ExtractOperation(output, video=True)

    job = op.build_job(context)

    assert job.map_streams == ["0:v:0"]
    assert job.copy_video is True


def test_extract_build_job_subtitles(
    context: OperationContext, tmp_path: Path
) -> None:
    output = tmp_path / "out.srt"
    op = ExtractOperation(output, subtitles=True)

    job = op.build_job(context)

    assert job.map_streams == ["0:s:0"]
    assert job.subtitle_codec == "copy"


def test_extract_finalize_sets_input_and_output(
    context: OperationContext, tmp_path: Path
) -> None:
    output = tmp_path / "out.mp3"
    op = ExtractOperation(output, audio=True)

    op.finalize(context)

    assert context.output_file == output
    assert context.input_file == output
