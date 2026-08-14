"""
Fast, pytest-based tests for RenderCache / CacheEntry.

Uses tmp_path for real (tiny) files so size_bytes/size_mb reflect
actual on-disk sizes rather than mocks.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from videoforge.media.render_cache import CacheEntry, RenderCache


# ---------------------------------------------------------------------
# CacheEntry
# ---------------------------------------------------------------------


def test_cache_entry_exists_and_size_for_real_file(tmp_path: Path) -> None:
    file_path = tmp_path / "thumb.png"
    file_path.write_bytes(b"x" * (3 * 1024 * 1024))  # 3MB, big enough to
    # survive size_mb's round-to-2-decimals without landing on 0.0

    entry = CacheEntry(path=file_path)

    assert entry.exists is True
    assert entry.size_bytes == 3 * 1024 * 1024
    assert entry.size_mb == pytest.approx(3.0, rel=1e-3)


def test_cache_entry_missing_file_reports_zero_size() -> None:
    entry = CacheEntry(path=Path("does/not/exist.png"))

    assert entry.exists is False
    assert entry.size_bytes == 0
    assert entry.size_mb == 0.0


# ---------------------------------------------------------------------
# Registration / lookup
# ---------------------------------------------------------------------


def test_render_cache_add_and_get_thumbnail(tmp_path: Path) -> None:
    cache = RenderCache()
    path = tmp_path / "thumb.png"
    path.write_bytes(b"x")

    cache.add_thumbnail("asset-1", path)

    entry = cache.get_thumbnail("asset-1")
    assert entry is not None
    assert entry.path == path
    assert cache.get_thumbnail("missing") is None


def test_render_cache_add_and_get_waveform(tmp_path: Path) -> None:
    cache = RenderCache()
    path = tmp_path / "wave.json"
    path.write_bytes(b"x")

    cache.add_waveform("asset-1", path)

    assert cache.get_waveform("asset-1") is not None
    assert cache.get_waveform("missing") is None


def test_render_cache_add_and_get_proxy(tmp_path: Path) -> None:
    cache = RenderCache()
    path = tmp_path / "proxy.mp4"
    path.write_bytes(b"x")

    cache.add_proxy("asset-1", path)

    assert cache.get_proxy("asset-1") is not None
    assert cache.get_proxy("missing") is None


def test_render_cache_add_preview_frame(tmp_path: Path) -> None:
    cache = RenderCache()
    path = tmp_path / "frame_0001.png"
    path.write_bytes(b"x")

    cache.add_preview_frame(1, path)

    assert cache.preview_frames[1].path == path
    assert cache.preview_frame_count == 1


# ---------------------------------------------------------------------
# Counts / is_empty
# ---------------------------------------------------------------------


def test_render_cache_is_empty_by_default() -> None:
    cache = RenderCache()
    assert cache.is_empty is True


def test_render_cache_counts_after_adding_entries(tmp_path: Path) -> None:
    cache = RenderCache()
    cache.add_thumbnail("a", tmp_path / "t.png")
    cache.add_waveform("a", tmp_path / "w.json")
    cache.add_proxy("a", tmp_path / "p.mp4")
    cache.add_preview_frame(1, tmp_path / "f.png")

    assert cache.thumbnail_count == 1
    assert cache.waveform_count == 1
    assert cache.proxy_count == 1
    assert cache.preview_frame_count == 1
    assert cache.is_empty is False


def test_render_cache_is_empty_ignores_some_groups() -> None:
    """
    Documents current behavior rather than an idealized one: is_empty
    only checks thumbnails/waveforms/proxies/preview_frames/
    preview_videos/filters/gpu. Populating rendered_frames,
    audio_cache, preview_audio, subtitles, or overlays alone does NOT
    flip is_empty to False, even though the cache clearly isn't empty.
    """
    cache = RenderCache()
    cache.rendered_frames[1] = CacheEntry(path=Path("frame.png"))
    cache.audio_cache["a"] = CacheEntry(path=Path("audio.wav"))
    cache.subtitles["a"] = CacheEntry(path=Path("subs.srt"))

    assert cache.is_empty is True  # documented gap, not asserted-correct


# ---------------------------------------------------------------------
# invalidate_asset / clear_*
# ---------------------------------------------------------------------


def test_render_cache_invalidate_asset_removes_matching_entries(
    tmp_path: Path,
) -> None:
    cache = RenderCache()
    cache.add_thumbnail("asset-1", tmp_path / "t.png")
    cache.add_waveform("asset-1", tmp_path / "w.json")
    cache.add_proxy("asset-1", tmp_path / "p.mp4")
    cache.audio_cache["asset-1"] = CacheEntry(path=tmp_path / "a.wav")
    cache.preview_videos["asset-1"] = CacheEntry(path=tmp_path / "pv.mp4")
    # a different asset should be untouched
    cache.add_thumbnail("asset-2", tmp_path / "t2.png")

    cache.invalidate_asset("asset-1")

    assert cache.get_thumbnail("asset-1") is None
    assert cache.get_waveform("asset-1") is None
    assert cache.get_proxy("asset-1") is None
    assert "asset-1" not in cache.audio_cache
    assert "asset-1" not in cache.preview_videos
    assert cache.get_thumbnail("asset-2") is not None


def test_render_cache_clear_preview(tmp_path: Path) -> None:
    cache = RenderCache()
    cache.add_preview_frame(1, tmp_path / "f.png")
    cache.rendered_frames[1] = CacheEntry(path=tmp_path / "r.png")
    cache.preview_videos["a"] = CacheEntry(path=tmp_path / "pv.mp4")
    cache.preview_audio["a"] = CacheEntry(path=tmp_path / "pa.wav")

    cache.clear_preview()

    assert cache.preview_frames == {}
    assert cache.rendered_frames == {}
    assert cache.preview_videos == {}
    assert cache.preview_audio == {}


def test_render_cache_clear_proxies(tmp_path: Path) -> None:
    cache = RenderCache()
    cache.add_proxy("a", tmp_path / "p.mp4")

    cache.clear_proxies()

    assert cache.proxies == {}


def test_render_cache_clear_gpu() -> None:
    cache = RenderCache()
    cache.gpu["texture-1"] = object()

    cache.clear_gpu()

    assert cache.gpu == {}


def test_render_cache_clear_resets_everything(tmp_path: Path) -> None:
    cache = RenderCache()
    cache.add_thumbnail("a", tmp_path / "t.png")
    cache.add_waveform("a", tmp_path / "w.json")
    cache.add_proxy("a", tmp_path / "p.mp4")
    cache.add_preview_frame(1, tmp_path / "f.png")
    cache.subtitles["a"] = CacheEntry(path=tmp_path / "s.srt")
    cache.overlays["a"] = CacheEntry(path=tmp_path / "o.png")
    cache.filters["blur"] = {"strength": 5}
    cache.gpu["tex"] = object()
    cache.metadata["k"] = "v"

    cache.clear()

    assert cache.is_empty is True
    assert cache.subtitles == {}
    assert cache.overlays == {}
    assert cache.filters == {}
    assert cache.metadata == {}


# ---------------------------------------------------------------------
# Aggregate size
# ---------------------------------------------------------------------


def test_render_cache_total_size_sums_real_files(tmp_path: Path) -> None:
    cache = RenderCache()

    thumb_path = tmp_path / "t.png"
    thumb_path.write_bytes(b"x" * (2 * 1024 * 1024))  # 2MB

    wave_path = tmp_path / "w.json"
    wave_path.write_bytes(b"x" * (1024 * 1024))  # 1MB

    cache.add_thumbnail("a", thumb_path)
    cache.add_waveform("a", wave_path)

    assert cache.total_size_bytes == 3 * 1024 * 1024
    assert cache.total_size_mb == pytest.approx(3.0, rel=1e-3)


def test_render_cache_total_size_ignores_missing_files(tmp_path: Path) -> None:
    cache = RenderCache()
    cache.add_thumbnail("a", tmp_path / "does_not_exist.png")

    assert cache.total_size_bytes == 0
