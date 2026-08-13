
"""
Tests for the FFmpeg command builder.
"""

from pathlib import Path

import pytest

from videoforge.ffmpeg.command import FFmpegCommandBuilder
from videoforge.ffmpeg.job import FFmpegJob


# ==========================================================
# Helpers
# ==========================================================


def build_job(
    input_file: Path,
    output_file: Path,
    **kwargs: object,
) -> FFmpegJob:
    """
    Create an FFmpegJob with the required file fields.
    """

    return FFmpegJob(
        inputs=[input_file],
        output=output_file,
        **kwargs,
    )


# ==========================================================
# Basic command construction
# ==========================================================


def test_build_basic_command() -> None:
    """
    The builder should create a minimal valid command.
    """

    job = build_job(
        Path("input.mp4"),
        Path("output.mp4"),
    )

    command = FFmpegCommandBuilder.build(job)

    assert Path(command[0]).stem.lower() == "ffmpeg"
    assert "-y" in command
    assert "-i" in command
    assert "input.mp4" in command
    assert command[-1] == "output.mp4"


def test_output_is_last_argument() -> None:
    """
    The output file must always be the final argument.

    FFmpegRunner relies on this when adding progress options.
    """

    job = build_job(
        Path("input.mp4"),
        Path("output.mp4"),
    )

    command = FFmpegCommandBuilder.build(job)

    assert command[-1] == "output.mp4"


def test_no_overwrite_uses_n() -> None:
    """
    overwrite=False should produce -n.
    """

    job = build_job(
        Path("input.mp4"),
        Path("output.mp4"),
        overwrite=False,
    )

    command = FFmpegCommandBuilder.build(job)

    assert "-n" in command
    assert "-y" not in command


# ==========================================================
# Inputs
# ==========================================================


def test_multiple_inputs() -> None:
    """
    Every explicitly supplied input should become an -i pair.
    """

    job = FFmpegJob(
        inputs=[
            Path("video.mp4"),
            Path("overlay.png"),
        ],
        output=Path("output.mp4"),
    )

    command = FFmpegCommandBuilder.build(job)

    input_indexes = [
        index
        for index, value in enumerate(command)
        if value == "-i"
    ]

    assert len(input_indexes) == 2

    assert "video.mp4" in command
    assert "overlay.png" in command


# ==========================================================
# Stream mapping
# ==========================================================


def test_stream_mapping() -> None:
    """
    Explicit stream mappings should become -map arguments.
    """

    job = build_job(
        Path("input.mp4"),
        Path("output.mp4"),
        map_streams=[
            "0:v:0",
            "0:a:0",
        ],
    )

    command = FFmpegCommandBuilder.build(job)

    assert command.count("-map") == 2

    assert "0:v:0" in command
    assert "0:a:0" in command


# ==========================================================
# Video filters
# ==========================================================


def test_video_filters() -> None:
    """
    Video filters should be joined into a single -vf chain.
    """

    job = build_job(
        Path("input.mp4"),
        Path("output.mp4"),
        video_filters=[
            "scale=1080:1920",
            "hflip",
        ],
    )

    command = FFmpegCommandBuilder.build(job)

    assert command.count("-vf") == 1

    vf_index = command.index("-vf")

    assert command[vf_index + 1] == (
        "scale=1080:1920,hflip"
    )


def test_audio_filters() -> None:
    """
    Audio filters should be joined into a single -af chain.
    """

    job = build_job(
        Path("input.mp4"),
        Path("output.mp4"),
        audio_filters=[
            "volume=0.8",
            "atempo=1.25",
        ],
    )

    command = FFmpegCommandBuilder.build(job)

    assert command.count("-af") == 1

    af_index = command.index("-af")

    assert command[af_index + 1] == (
        "volume=0.8,atempo=1.25"
    )


def test_complex_filter_takes_precedence() -> None:
    """
    filter_complex should be emitted instead of -vf.
    """

    job = build_job(
        Path("input.mp4"),
        Path("output.mp4"),
        filter_complex=(
            "[0:v][1:v]overlay=10:10[outv]"
        ),
        video_filters=[
            "scale=720:1280",
        ],
    )

    command = FFmpegCommandBuilder.build(job)

    assert "-filter_complex" in command
    assert "-vf" not in command

    filter_index = command.index(
        "-filter_complex"
    )

    assert command[filter_index + 1] == (
        "[0:v][1:v]overlay=10:10[outv]"
    )


# ==========================================================
# Codecs
# ==========================================================


def test_video_codec() -> None:
    """
    video_codec should become -c:v.
    """

    job = build_job(
        Path("input.mp4"),
        Path("output.mp4"),
        video_codec="libx264",
    )

    command = FFmpegCommandBuilder.build(job)

    codec_index = command.index("-c:v")

    assert command[codec_index + 1] == "libx264"


def test_audio_codec() -> None:
    """
    audio_codec should become -c:a.
    """

    job = build_job(
        Path("input.mp4"),
        Path("output.mp4"),
        audio_codec="aac",
    )

    command = FFmpegCommandBuilder.build(job)

    codec_index = command.index("-c:a")

    assert command[codec_index + 1] == "aac"


def test_copy_video() -> None:
    """
    copy_video should produce -c:v copy.
    """

    job = build_job(
        Path("input.mp4"),
        Path("output.mp4"),
        copy_video=True,
    )

    command = FFmpegCommandBuilder.build(job)

    codec_index = command.index("-c:v")

    assert command[codec_index + 1] == "copy"


def test_copy_audio() -> None:
    """
    copy_audio should produce -c:a copy.
    """

    job = build_job(
        Path("input.mp4"),
        Path("output.mp4"),
        copy_audio=True,
    )

    command = FFmpegCommandBuilder.build(job)

    codec_index = command.index("-c:a")

    assert command[codec_index + 1] == "copy"


def test_subtitle_codec() -> None:
    """
    subtitle_codec should become -c:s.
    """

    job = build_job(
        Path("input.mkv"),
        Path("output.mkv"),
        subtitle_codec="copy",
    )

    command = FFmpegCommandBuilder.build(job)

    codec_index = command.index("-c:s")

    assert command[codec_index + 1] == "copy"


# ==========================================================
# Encoding options
# ==========================================================


def test_encoding_options() -> None:
    """
    Encoding parameters should be translated correctly.
    """

    job = build_job(
        Path("input.mp4"),
        Path("output.mp4"),
        video_codec="libx264",
        audio_codec="aac",
        preset="medium",
        crf=23,
        video_bitrate="5M",
        audio_bitrate="192k",
        pixel_format="yuv420p",
        profile="high",
        level="4.1",
        tune="film",
    )

    command = FFmpegCommandBuilder.build(job)

    assert "-preset" in command
    assert command[
        command.index("-preset") + 1
    ] == "medium"

    assert "-crf" in command
    assert command[
        command.index("-crf") + 1
    ] == "23"

    assert "-b:v" in command
    assert command[
        command.index("-b:v") + 1
    ] == "5M"

    assert "-b:a" in command
    assert command[
        command.index("-b:a") + 1
    ] == "192k"

    assert "-pix_fmt" in command
    assert command[
        command.index("-pix_fmt") + 1
    ] == "yuv420p"

    assert "-profile:v" in command
    assert command[
        command.index("-profile:v") + 1
    ] == "high"

    assert "-level" in command
    assert command[
        command.index("-level") + 1
    ] == "4.1"

    assert "-tune" in command
    assert command[
        command.index("-tune") + 1
    ] == "film"


# ==========================================================
# Timing
# ==========================================================


def test_start_time() -> None:
    """
    start_time should become -ss.
    """

    job = build_job(
        Path("input.mp4"),
        Path("output.mp4"),
        start_time=10.5,
    )

    command = FFmpegCommandBuilder.build(job)

    index = command.index("-ss")

    assert command[index + 1] == "10.5"


def test_duration() -> None:
    """
    duration should become -t.
    """

    job = build_job(
        Path("input.mp4"),
        Path("output.mp4"),
        duration=15.0,
    )

    command = FFmpegCommandBuilder.build(job)

    index = command.index("-t")

    assert command[index + 1] == "15.0"


def test_end_time() -> None:
    """
    end_time should become -to when duration is absent.
    """

    job = build_job(
        Path("input.mp4"),
        Path("output.mp4"),
        end_time=30.0,
    )

    command = FFmpegCommandBuilder.build(job)

    index = command.index("-to")

    assert command[index + 1] == "30.0"


def test_duration_takes_precedence_over_end_time() -> None:
    """
    duration should be used instead of -to when both are supplied.
    """

    job = build_job(
        Path("input.mp4"),
        Path("output.mp4"),
        duration=15.0,
        end_time=30.0,
    )

    command = FFmpegCommandBuilder.build(job)

    assert "-t" in command
    assert "-to" not in command


def test_frame_rate() -> None:
    """
    frame_rate should become -r.
    """

    job = build_job(
        Path("input.mp4"),
        Path("output.mp4"),
        frame_rate=30.0,
    )

    command = FFmpegCommandBuilder.build(job)

    index = command.index("-r")

    assert command[index + 1] == "30.0"


# ==========================================================
# Audio options
# ==========================================================


def test_audio_options() -> None:
    """
    Audio configuration should be translated correctly.
    """

    job = build_job(
        Path("input.mp4"),
        Path("output.mp4"),
        sample_rate=48000,
        channels=2,
    )

    command = FFmpegCommandBuilder.build(job)

    assert "-ar" in command
    assert command[
        command.index("-ar") + 1
    ] == "48000"

    assert "-ac" in command
    assert command[
        command.index("-ac") + 1
    ] == "2"


def test_volume() -> None:
    """
    volume should produce an audio volume filter.
    """

    job = build_job(
        Path("input.mp4"),
        Path("output.mp4"),
        volume=0.75,
    )

    command = FFmpegCommandBuilder.build(job)

    assert "-af" in command

    index = command.index("-af")

    assert command[index + 1] == "volume=0.75"


# ==========================================================
# Hardware acceleration
# ==========================================================


def test_hardware_acceleration() -> None:
    """
    Hardware acceleration options should be emitted.
    """

    job = build_job(
        Path("input.mp4"),
        Path("output.mp4"),
        hwaccel="cuda",
        hwaccel_output_format="cuda",
    )

    command = FFmpegCommandBuilder.build(job)

    assert "-hwaccel" in command
    assert command[
        command.index("-hwaccel") + 1
    ] == "cuda"

    assert "-hwaccel_output_format" in command
    assert command[
        command.index("-hwaccel_output_format") + 1
    ] == "cuda"


# ==========================================================
# Metadata
# ==========================================================


def test_metadata() -> None:
    """
    Metadata should become -metadata arguments.
    """

    job = build_job(
        Path("input.mp4"),
        Path("output.mp4"),
        metadata={
            "title": "VideoForge Test",
            "artist": "VideoForge",
        },
    )

    command = FFmpegCommandBuilder.build(job)

    assert command.count("-metadata") == 2

    assert "title=VideoForge Test" in command
    assert "artist=VideoForge" in command


# ==========================================================
# Threads
# ==========================================================


def test_threads() -> None:
    """
    threads should become -threads.
    """

    job = build_job(
        Path("input.mp4"),
        Path("output.mp4"),
        threads=4,
    )

    command = FFmpegCommandBuilder.build(job)

    index = command.index("-threads")

    assert command[index + 1] == "4"


# ==========================================================
# Extra arguments
# ==========================================================


def test_extra_args() -> None:
    """
    extra_args should be appended before the output file.
    """

    job = build_job(
        Path("input.mp4"),
        Path("output.mp4"),
        extra_args=[
            "-movflags",
            "+faststart",
        ],
    )

    command = FFmpegCommandBuilder.build(job)

    assert "-movflags" in command
    assert "+faststart" in command

    assert command[-1] == "output.mp4"


# ==========================================================
# Subtitle burning
# ==========================================================


def test_burn_subtitles_requires_subtitle_file() -> None:
    """
    burn_subtitles=True requires subtitle_file.
    """

    job = build_job(
        Path("input.mp4"),
        Path("output.mp4"),
        burn_subtitles=True,
    )

    with pytest.raises(
        ValueError,
        match="subtitle_file",
    ):
        FFmpegCommandBuilder.build(job)


def test_burn_subtitles() -> None:
    """
    Burn subtitles should produce a subtitles video filter.
    """

    job = build_job(
        Path("input.mp4"),
        Path("output.mp4"),
        subtitle_file=Path("captions.srt"),
        burn_subtitles=True,
    )

    command = FFmpegCommandBuilder.build(job)

    assert "-vf" in command

    index = command.index("-vf")

    assert "subtitles=" in command[index + 1]
    assert "captions.srt" in command[index + 1]


def test_burn_subtitles_with_style() -> None:
    """
    subtitle_force_style metadata should be translated into
    the subtitles filter's force_style parameter.
    """

    job = build_job(
        Path("input.mp4"),
        Path("output.mp4"),
        subtitle_file=Path("captions.ass"),
        burn_subtitles=True,
        metadata={
            "subtitle_force_style": (
                "FontName=Arial,FontSize=26"
            ),
        },
    )

    command = FFmpegCommandBuilder.build(job)

    assert "-vf" in command

    index = command.index("-vf")

    subtitle_filter = command[index + 1]

    assert "subtitles=" in subtitle_filter
    assert "force_style=" in subtitle_filter
    assert "FontName=Arial" in subtitle_filter


# ==========================================================
# Output ordering
# ==========================================================


def test_output_remains_last_with_many_options() -> None:
    """
    The output path must remain last regardless of job options.
    """

    job = build_job(
        Path("input.mp4"),
        Path("output.mp4"),
        video_filters=[
            "scale=1080:1920",
            "hflip",
        ],
        audio_filters=[
            "volume=0.8",
        ],
        video_codec="libx264",
        audio_codec="aac",
        preset="medium",
        crf=23,
        start_time=5,
        duration=20,
        frame_rate=30,
        sample_rate=48000,
        channels=2,
        threads=4,
        metadata={
            "title": "Test",
        },
        extra_args=[
            "-movflags",
            "+faststart",
        ],
    )

    command = FFmpegCommandBuilder.build(job)

    assert command[-1] == "output.mp4"
