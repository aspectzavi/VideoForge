"""
Fast, pytest-based tests for MediaAsset.

Where a computed property requires probed media info, MediaAsset.probe
is patched with a hand-built MediaInfo rather than invoking real
ffprobe, so these tests stay fast and deterministic.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from videoforge.ffmpeg.probe import MediaFormat, MediaInfo, VideoStream
from videoforge.media.asset import MediaAsset

SAMPLE_MEDIA = Path("tests/sample_media/input.mp4")


@pytest.fixture
def fake_media_info() -> MediaInfo:
    return MediaInfo(
        format=MediaFormat(filename=str(SAMPLE_MEDIA), duration=12.5),
        videos=[
            VideoStream(
                index=0,
                width=1920,
                height=1080,
                frame_rate="30/1",
            )
        ],
        audios=[],
    )


# ---------------------------------------------------------------------
# Construction / file properties (no probing involved)
# ---------------------------------------------------------------------


def test_asset_load_sets_path() -> None:
    asset = MediaAsset.load(SAMPLE_MEDIA)

    assert asset.path == SAMPLE_MEDIA
    assert asset.filename == "input.mp4"
    assert asset.stem == "input"
    assert asset.suffix == ".mp4"
    assert asset.extension == "mp4"


def test_asset_exists_reflects_real_file() -> None:
    real = MediaAsset.load(SAMPLE_MEDIA)
    missing = MediaAsset.load("tests/sample_media/does_not_exist.mp4")

    assert real.exists is True
    assert missing.exists is False
    assert missing.size_bytes == 0


@pytest.mark.parametrize(
    "filename,expected_type",
    [
        ("clip.mp4", "video"),
        ("clip.mov", "video"),
        ("clip.mkv", "video"),
        ("song.mp3", "audio"),
        ("song.wav", "audio"),
        ("photo.png", "image"),
        ("photo.jpg", "image"),
        ("anim.gif", "gif"),
        ("weird.xyz", "unknown"),
    ],
)
def test_asset_type_detection(filename: str, expected_type: str) -> None:
    asset = MediaAsset.load(f"tests/sample_media/{filename}")

    assert asset.asset_type == expected_type
    assert asset.is_video == (expected_type == "video")
    assert asset.is_audio == (expected_type == "audio")
    assert asset.is_image == (expected_type == "image")
    assert asset.is_gif == (expected_type == "gif")


# ---------------------------------------------------------------------
# Probed media properties (mocked, no real ffprobe)
# ---------------------------------------------------------------------


def test_asset_probed_properties_use_media_info(
    fake_media_info: MediaInfo,
) -> None:
    asset = MediaAsset.load(SAMPLE_MEDIA)

    with patch(
        "videoforge.media.asset.probe.probe",
        return_value=fake_media_info,
    ) as mock_probe:
        assert asset.duration == pytest.approx(12.5)
        assert asset.width == 1920
        assert asset.height == 1080
        assert asset.fps == pytest.approx(30.0)
        assert asset.has_audio is False

    # probe() is only called once; media_info is cached afterward.
    mock_probe.assert_called_once_with(SAMPLE_MEDIA)


def test_asset_refresh_forces_reprobe(fake_media_info: MediaInfo) -> None:
    asset = MediaAsset.load(SAMPLE_MEDIA)
    asset.media_info = fake_media_info

    updated = fake_media_info.model_copy(deep=True)
    updated.format.duration = 99.0

    with patch(
        "videoforge.media.asset.probe.probe",
        return_value=updated,
    ) as mock_probe:
        asset.refresh()

    mock_probe.assert_called_once_with(SAMPLE_MEDIA)
    assert asset.duration == pytest.approx(99.0)


# ---------------------------------------------------------------------
# Tags / rating / favorite / proxy
# ---------------------------------------------------------------------


def test_asset_tag_management() -> None:
    asset = MediaAsset.load(SAMPLE_MEDIA)

    asset.add_tag("b-roll")
    asset.add_tag("b-roll")  # duplicate, ignored
    asset.add_tag("interview")

    assert asset.tags == ["b-roll", "interview"]

    removed = asset.remove_tag("b-roll")
    missing = asset.remove_tag("not-there")

    assert removed is True
    assert missing is False
    assert asset.tags == ["interview"]

    asset.clear_tags()

    assert asset.tags == []


def test_asset_rating_is_clamped_0_to_5() -> None:
    asset = MediaAsset.load(SAMPLE_MEDIA)

    asset.set_rating(3)
    assert asset.rating == 3

    asset.set_rating(10)
    assert asset.rating == 5

    asset.set_rating(-4)
    assert asset.rating == 0


def test_asset_favorite_toggle() -> None:
    asset = MediaAsset.load(SAMPLE_MEDIA)

    assert asset.favorite is False

    asset.favorite_asset()
    assert asset.favorite is True

    asset.unfavorite_asset()
    assert asset.favorite is False


def test_asset_proxy_management() -> None:
    asset = MediaAsset.load(SAMPLE_MEDIA)

    assert asset.has_proxy is False

    asset.set_proxy("tests/sample_media/does_not_exist_proxy.mp4")

    # proxy_path is set, but has_proxy also requires the file to exist.
    assert asset.proxy_path == Path("tests/sample_media/does_not_exist_proxy.mp4")
    assert asset.has_proxy is False

    asset.set_proxy(SAMPLE_MEDIA)
    assert asset.has_proxy is True

    asset.remove_proxy()
    assert asset.proxy_path is None
    assert asset.has_proxy is False


# ---------------------------------------------------------------------
# Cloning / serialization
# ---------------------------------------------------------------------


def test_asset_clone_gets_new_id_and_is_independent() -> None:
    original = MediaAsset.load(SAMPLE_MEDIA)
    original.add_tag("original")

    clone = original.clone()

    assert clone.id != original.id
    assert clone.path == original.path

    clone.add_tag("clone-only")

    assert "clone-only" not in original.tags


def test_asset_to_dict_triggers_probe_and_stabilizes_on_second_call() -> None:
    """
    Documents a real quirk rather than asserting an idealized one:
    to_dict()/model_dump() serialize Pydantic computed_field properties,
    and MediaAsset's duration/width/height/etc. properties lazily call
    self.probe() (a real ffprobe subprocess) on first access if
    media_info is None. Because the plain `media_info` field is
    declared, and therefore serialized, *before* those computed
    properties in the class body, the FIRST to_dict()/model_dump() call
    on an unprobed asset embeds a stale `media_info: None` even though
    probing happens during that same call and duration/width/etc. show
    real values. A second call is fully self-consistent. Also worth
    noting for callers: a plain serialization call can silently shell
    out to ffprobe the first time it's used on an unprobed asset.
    """
    asset = MediaAsset.load(SAMPLE_MEDIA)

    first = asset.to_dict()

    assert first["media_info"] is None
    assert first["duration"] > 0  # the real ffprobe call already ran
    assert asset.media_info is not None  # side effect landed on the asset

    second = asset.to_dict()

    assert second == asset.model_dump()
    assert second["media_info"] is not None
    assert second["path"] == SAMPLE_MEDIA
