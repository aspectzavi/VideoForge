"""
Integration tests for the new audio/export operations, run against
real FFmpeg on the real sample clip.

These prove the generated FFmpeg commands are actually valid, not
just that the FFmpegJob objects look right in isolation. All are kept
fast: audio operations stream-copy video (copy_video=True) instead of
re-encoding the full clip, and export operations only ever produce a
single frame, a short GIF clip, or a tiny sprite sheet.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from videoforge.ffmpeg.pipeline import Pipeline
from videoforge.operations.audio.extract_audio import ExtractAudioOperation
from videoforge.operations.audio.fade import AudioFadeOperation
from videoforge.operations.audio.mix import MixAudioOperation
from videoforge.operations.audio.mute import MuteOperation
from videoforge.operations.audio.normalize import NormalizeAudioOperation
from videoforge.operations.audio.replace_audio import ReplaceAudioOperation
from videoforge.operations.audio.volume import VolumeOperation
from videoforge.operations.export.gif import GifOperation
from videoforge.operations.export.proxy import ProxyOperation
from videoforge.operations.export.spritesheet import SpritesheetOperation
from videoforge.operations.export.thumbnail import ThumbnailOperation
from videoforge.operations.video.trim import TrimOperation

SAMPLE_INPUT = Path("tests/sample_media/input.mp4")


@pytest.fixture(scope="module")
def short_clip() -> Path:
    """
    A real ~3s trimmed clip, produced once per test module run, used
    as the input for every test below so nothing operates on the full
    86s sample unnecessarily.
    """
    result = Pipeline().add(TrimOperation(0.0, 3.0)).run(SAMPLE_INPUT)
    assert result.success
    return result.context.input_file


@pytest.fixture(scope="module")
def extracted_audio(short_clip: Path, tmp_path_factory: pytest.TempPathFactory) -> Path:
    """
    A real short audio file extracted from short_clip, used as the
    "external" audio track for mix/replace_audio tests.
    """
    tmp_dir = tmp_path_factory.mktemp("extracted_audio")
    output = tmp_dir / "extracted.aac"

    ctx_result = Pipeline().add(ExtractAudioOperation(output)).run(short_clip)
    assert ctx_result.success
    assert output.exists()

    return output


# ---------------------------------------------------------------------
# Audio operations
# ---------------------------------------------------------------------


@pytest.mark.integration
def test_real_volume_operation(short_clip: Path) -> None:
    result = Pipeline().add(VolumeOperation(0.5)).run(short_clip)

    assert result.success
    assert result.context.input_file.exists()
    assert result.context.input_file.stat().st_size > 0


@pytest.mark.integration
def test_real_mute_operation(short_clip: Path) -> None:
    result = Pipeline().add(MuteOperation()).run(short_clip)

    assert result.success
    assert result.context.input_file.exists()


@pytest.mark.integration
def test_real_fade_operation(short_clip: Path) -> None:
    op = AudioFadeOperation(fade_in=0.5, fade_out=0.5, total_duration=3.0)
    result = Pipeline().add(op).run(short_clip)

    assert result.success
    assert result.context.input_file.exists()


@pytest.mark.integration
def test_real_normalize_operation(short_clip: Path) -> None:
    result = Pipeline().add(NormalizeAudioOperation()).run(short_clip)

    assert result.success
    assert result.context.input_file.exists()


@pytest.mark.integration
def test_real_mix_operation(short_clip: Path, extracted_audio: Path) -> None:
    op = MixAudioOperation(extracted_audio, mix_volume=0.5)
    result = Pipeline().add(op).run(short_clip)

    assert result.success
    assert result.context.input_file.exists()


@pytest.mark.integration
def test_real_replace_audio_operation(short_clip: Path, extracted_audio: Path) -> None:
    op = ReplaceAudioOperation(extracted_audio)
    result = Pipeline().add(op).run(short_clip)

    assert result.success
    assert result.context.input_file.exists()


@pytest.mark.integration
def test_real_extract_audio_operation(short_clip: Path, tmp_path: Path) -> None:
    output = tmp_path / "audio.mp3"
    op = ExtractAudioOperation(output, audio_codec="libmp3lame")
    result = Pipeline().add(op).run(short_clip)

    assert result.success
    assert output.exists()
    assert output.stat().st_size > 0


# ---------------------------------------------------------------------
# Export operations
# ---------------------------------------------------------------------


@pytest.mark.integration
def test_real_thumbnail_operation(short_clip: Path, tmp_path: Path) -> None:
    output = tmp_path / "thumb.jpg"
    op = ThumbnailOperation(output, time=1.0, width=320)
    result = Pipeline().add(op).run(short_clip)

    assert result.success
    assert output.exists()
    assert output.stat().st_size > 0
    assert result.context.data["thumbnail_file"] == output


@pytest.mark.integration
def test_real_gif_operation(short_clip: Path, tmp_path: Path) -> None:
    output = tmp_path / "out.gif"
    op = GifOperation(output, duration=1.5, fps=8, width=160)
    result = Pipeline().add(op).run(short_clip)

    assert result.success
    assert output.exists()
    assert output.stat().st_size > 0
    assert result.context.data["gif_file"] == output


@pytest.mark.integration
def test_real_spritesheet_operation(short_clip: Path, tmp_path: Path) -> None:
    output = tmp_path / "sheet.jpg"
    op = SpritesheetOperation(output, columns=2, rows=2, interval=0.5, thumb_width=80)
    result = Pipeline().add(op).run(short_clip)

    assert result.success
    assert output.exists()
    assert output.stat().st_size > 0
    assert result.context.data["spritesheet_file"] == output


@pytest.mark.integration
def test_real_proxy_operation(short_clip: Path, tmp_path: Path) -> None:
    output = tmp_path / "proxy.mp4"
    op = ProxyOperation(output, width=320, preset="ultrafast")
    result = Pipeline().add(op).run(short_clip)

    assert result.success
    assert output.exists()
    assert output.stat().st_size > 0
    assert result.context.data["proxy_file"] == output
