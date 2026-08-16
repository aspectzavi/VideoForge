"""
Fast, pytest-based tests for operations/audio/*.py.

All prepare() methods here that reference a second file (mix,
replace_audio) do real filesystem existence checks, so tests use
tmp_path for those. No FFmpeg subprocess is ever spawned - build_job()
only constructs FFmpegJob objects.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from videoforge.operations.audio.extract_audio import ExtractAudioOperation
from videoforge.operations.audio.fade import AudioFadeOperation
from videoforge.operations.audio.mix import MixAudioOperation
from videoforge.operations.audio.mute import MuteOperation
from videoforge.operations.audio.normalize import NormalizeAudioOperation
from videoforge.operations.audio.replace_audio import ReplaceAudioOperation
from videoforge.operations.audio.volume import VolumeOperation
from videoforge.operations.base import OperationContext


@pytest.fixture
def input_video(tmp_path: Path) -> Path:
    p = tmp_path / "input.mp4"
    p.write_bytes(b"fake video")
    return p


@pytest.fixture
def audio_file(tmp_path: Path) -> Path:
    p = tmp_path / "music.mp3"
    p.write_bytes(b"fake audio")
    return p


@pytest.fixture
def context(input_video: Path) -> OperationContext:
    return OperationContext(input_file=input_video)


# ---------------------------------------------------------------------
# VolumeOperation
# ---------------------------------------------------------------------


def test_volume_builds_filter(context: OperationContext) -> None:
    job = VolumeOperation(0.5).build_job(context)
    assert job.audio_filters == ["volume=0.5"]
    assert job.copy_video is True


def test_volume_does_not_set_job_volume_field(context: OperationContext) -> None:
    # Guards against the -af/-af collision documented in volume.py:
    # only audio_filters should be used, never FFmpegJob.volume too.
    job = VolumeOperation(2.0).build_job(context)
    assert job.volume is None


def test_volume_rejects_negative_level() -> None:
    with pytest.raises(ValueError):
        VolumeOperation(-1.0)


# ---------------------------------------------------------------------
# MuteOperation
# ---------------------------------------------------------------------


def test_mute_strips_audio_and_copies_video(context: OperationContext) -> None:
    job = MuteOperation().build_job(context)

    assert job.copy_video is True
    assert "-an" in job.extra_args


# ---------------------------------------------------------------------
# AudioFadeOperation
# ---------------------------------------------------------------------


def test_fade_in_only(context: OperationContext) -> None:
    job = AudioFadeOperation(fade_in=2.0).build_job(context)
    assert job.audio_filters == ["afade=t=in:st=0:d=2.0"]
    assert job.copy_video is True


def test_fade_out_only(context: OperationContext) -> None:
    job = AudioFadeOperation(fade_out=3.0, total_duration=20.0).build_job(context)
    assert job.audio_filters == ["afade=t=out:st=17.0:d=3.0"]


def test_fade_in_and_out(context: OperationContext) -> None:
    op = AudioFadeOperation(fade_in=1.0, fade_out=2.0, total_duration=10.0)
    job = op.build_job(context)

    assert job.audio_filters == [
        "afade=t=in:st=0:d=1.0",
        "afade=t=out:st=8.0:d=2.0",
    ]


def test_fade_rejects_both_zero() -> None:
    with pytest.raises(ValueError, match="At least one"):
        AudioFadeOperation()


def test_fade_out_requires_total_duration() -> None:
    with pytest.raises(ValueError, match="total_duration is required"):
        AudioFadeOperation(fade_out=2.0)


def test_fade_out_rejects_longer_than_total_duration() -> None:
    with pytest.raises(ValueError, match="cannot be longer"):
        AudioFadeOperation(fade_out=15.0, total_duration=10.0)


def test_fade_rejects_negative_durations() -> None:
    with pytest.raises(ValueError):
        AudioFadeOperation(fade_in=-1.0)

    with pytest.raises(ValueError):
        AudioFadeOperation(fade_out=-1.0, total_duration=10.0)


# ---------------------------------------------------------------------
# NormalizeAudioOperation
# ---------------------------------------------------------------------


def test_normalize_builds_loudnorm_filter(context: OperationContext) -> None:
    op = NormalizeAudioOperation(target_loudness=-16.0, true_peak=-1.5, loudness_range=11.0)
    job = op.build_job(context)

    assert job.audio_filters == ["loudnorm=I=-16.0:TP=-1.5:LRA=11.0"]
    assert job.copy_video is True


def test_normalize_defaults_to_ebu_r128() -> None:
    op = NormalizeAudioOperation()
    assert op.target_loudness == -23.0
    assert op.true_peak == -2.0
    assert op.loudness_range == 7.0


def test_normalize_rejects_nonpositive_loudness_range() -> None:
    with pytest.raises(ValueError):
        NormalizeAudioOperation(loudness_range=0)

    with pytest.raises(ValueError):
        NormalizeAudioOperation(loudness_range=-1)


# ---------------------------------------------------------------------
# MixAudioOperation
# ---------------------------------------------------------------------


def test_mix_prepare_validates_audio_file_exists(
    context: OperationContext, audio_file: Path
) -> None:
    op = MixAudioOperation(audio_file)
    op.prepare(context)  # should not raise


def test_mix_prepare_rejects_missing_audio_file(
    context: OperationContext, tmp_path: Path
) -> None:
    op = MixAudioOperation(tmp_path / "missing.mp3")

    with pytest.raises(FileNotFoundError):
        op.prepare(context)


def test_mix_rejects_invalid_duration_mode(audio_file: Path) -> None:
    with pytest.raises(ValueError, match="duration must be one of"):
        MixAudioOperation(audio_file, duration="average")


def test_mix_rejects_negative_volumes(audio_file: Path) -> None:
    with pytest.raises(ValueError):
        MixAudioOperation(audio_file, mix_volume=-1.0)

    with pytest.raises(ValueError):
        MixAudioOperation(audio_file, original_volume=-1.0)


def test_mix_build_job_constructs_filter_complex_and_mapping(
    context: OperationContext, audio_file: Path
) -> None:
    op = MixAudioOperation(audio_file, mix_volume=0.8, original_volume=1.0, duration="shortest")

    job = op.build_job(context)

    assert job.inputs == [context.input_file, audio_file]
    assert job.filter_complex == (
        "[0:a]volume=1.0[a0];[1:a]volume=0.8[a1];[a0][a1]amix=inputs=2:duration=shortest[aout]"
    )
    assert job.map_streams == ["0:v?", "[aout]"]
    assert job.copy_video is True


# ---------------------------------------------------------------------
# ReplaceAudioOperation
# ---------------------------------------------------------------------


def test_replace_audio_prepare_validates_file_exists(
    context: OperationContext, audio_file: Path
) -> None:
    op = ReplaceAudioOperation(audio_file)
    op.prepare(context)  # should not raise


def test_replace_audio_prepare_rejects_missing_file(
    context: OperationContext, tmp_path: Path
) -> None:
    op = ReplaceAudioOperation(tmp_path / "missing.mp3")

    with pytest.raises(FileNotFoundError):
        op.prepare(context)


def test_replace_audio_build_job_maps_video_and_new_audio(
    context: OperationContext, audio_file: Path
) -> None:
    op = ReplaceAudioOperation(audio_file)
    job = op.build_job(context)

    assert job.inputs == [context.input_file, audio_file]
    assert job.map_streams == ["0:v?", "1:a:0"]
    assert job.copy_video is True
    assert job.extra_args == []


def test_replace_audio_trim_to_shortest_adds_flag(
    context: OperationContext, audio_file: Path
) -> None:
    op = ReplaceAudioOperation(audio_file, trim_to_shortest=True)
    job = op.build_job(context)

    assert job.extra_args == ["-shortest"]


# ---------------------------------------------------------------------
# ExtractAudioOperation
# ---------------------------------------------------------------------


def test_extract_audio_prepare_validates_and_stores_path(
    context: OperationContext, tmp_path: Path
) -> None:
    output = tmp_path / "audio.mp3"
    op = ExtractAudioOperation(output)

    op.prepare(context)

    assert context.data["extracted_audio_file"] == output


def test_extract_audio_prepare_rejects_missing_input(tmp_path: Path) -> None:
    ctx = OperationContext(input_file=tmp_path / "missing.mp4")
    op = ExtractAudioOperation(tmp_path / "audio.mp3")

    with pytest.raises(FileNotFoundError):
        op.prepare(ctx)


def test_extract_audio_prepare_rejects_output_equal_to_input(
    input_video: Path,
) -> None:
    ctx = OperationContext(input_file=input_video)
    op = ExtractAudioOperation(input_video)

    with pytest.raises(ValueError, match="different from the input"):
        op.prepare(ctx)


def test_extract_audio_build_job_copies_by_default(
    context: OperationContext, tmp_path: Path
) -> None:
    output = tmp_path / "audio.aac"
    op = ExtractAudioOperation(output)

    job = op.build_job(context)

    assert job.output == output
    assert job.map_streams == ["0:a:0"]
    assert job.copy_audio is True
    assert job.audio_codec is None


def test_extract_audio_build_job_reencodes_when_codec_given(
    context: OperationContext, tmp_path: Path
) -> None:
    output = tmp_path / "audio.mp3"
    op = ExtractAudioOperation(
        output, audio_codec="libmp3lame", bitrate="192k", sample_rate=44100
    )

    job = op.build_job(context)

    assert job.copy_audio is False
    assert job.audio_codec == "libmp3lame"
    assert job.audio_bitrate == "192k"
    assert job.sample_rate == 44100


def test_extract_audio_finalize_does_not_touch_input_file(
    context: OperationContext, tmp_path: Path
) -> None:
    output = tmp_path / "audio.mp3"
    op = ExtractAudioOperation(output)
    original_input = context.input_file

    op.finalize(context)

    assert context.data["extracted_audio_file"] == output
    assert context.input_file == original_input  # unchanged - not advanced
    assert context.output_file is None
