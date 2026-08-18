"""
Fast, pytest-based tests for MediaProxy (media/proxy.py).

Uses real tmp_path files for exists/size_bytes checks.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from videoforge.media.proxy import MediaProxy, ProxyStatus


def _proxy(tmp_path: Path, proxy_exists: bool = False) -> MediaProxy:
    original = tmp_path / "original.mp4"
    original.write_bytes(b"x")

    proxy_path = tmp_path / "proxy.mp4"

    if proxy_exists:
        proxy_path.write_bytes(b"x" * (2 * 1024 * 1024))  # 2MB

    return MediaProxy(asset_id="a1", original_path=original, proxy_path=proxy_path)


def test_defaults(tmp_path: Path) -> None:
    proxy = _proxy(tmp_path)

    assert proxy.status == ProxyStatus.PENDING
    assert proxy.is_pending is True
    assert proxy.exists is False
    assert proxy.size_bytes == 0
    assert proxy.original_exists is True
    assert proxy.resolution is None


def test_resolution_when_dimensions_set(tmp_path: Path) -> None:
    proxy = _proxy(tmp_path)
    proxy.width = 1280
    proxy.height = 720

    assert proxy.resolution == "1280x720"


def test_status_transitions(tmp_path: Path) -> None:
    proxy = _proxy(tmp_path)

    proxy.mark_generating()
    assert proxy.is_generating is True

    proxy.mark_ready()
    assert proxy.status == ProxyStatus.READY
    assert proxy.completed_at is not None

    proxy.mark_failed()
    assert proxy.is_failed is True

    proxy.mark_missing()
    assert proxy.is_missing is True

    proxy.mark_pending()
    assert proxy.is_pending is True


def test_is_ready_requires_status_and_file(tmp_path: Path) -> None:
    proxy = _proxy(tmp_path, proxy_exists=True)

    proxy.mark_ready()
    assert proxy.is_ready is True

    proxy.proxy_path.unlink()
    assert proxy.exists is False
    assert proxy.is_ready is False  # status says ready, but file is gone


def test_size_bytes_and_mb_for_real_file(tmp_path: Path) -> None:
    proxy = _proxy(tmp_path, proxy_exists=True)

    assert proxy.size_bytes == 2 * 1024 * 1024
    assert proxy.size_mb == pytest.approx(2.0)


def test_active_path_prefers_proxy_when_ready(tmp_path: Path) -> None:
    proxy = _proxy(tmp_path, proxy_exists=True)

    assert proxy.active_path == proxy.original_path  # not ready yet

    proxy.mark_ready()
    assert proxy.active_path == proxy.proxy_path


def test_relink_updates_path_and_refreshes_status(tmp_path: Path) -> None:
    proxy = _proxy(tmp_path)
    new_path = tmp_path / "new_proxy.mp4"
    new_path.write_bytes(b"x")

    proxy.relink(new_path)

    assert proxy.proxy_path == new_path
    assert proxy.status == ProxyStatus.READY  # refresh() promotes PENDING -> READY


def test_refresh_demotes_ready_to_missing_when_file_gone(tmp_path: Path) -> None:
    proxy = _proxy(tmp_path, proxy_exists=True)
    proxy.mark_ready()

    proxy.proxy_path.unlink()
    proxy.refresh()

    assert proxy.status == ProxyStatus.MISSING


def test_delete_removes_file_and_marks_missing(tmp_path: Path) -> None:
    proxy = _proxy(tmp_path, proxy_exists=True)
    proxy.mark_ready()

    proxy.delete()

    assert proxy.proxy_path.exists() is False
    assert proxy.status == ProxyStatus.MISSING
    assert proxy.completed_at is None


def test_metadata_helpers(tmp_path: Path) -> None:
    proxy = _proxy(tmp_path)

    proxy.set_metadata("codec", "h264")
    assert proxy.get_metadata("codec") == "h264"
    assert proxy.get_metadata("missing", "default") == "default"

    proxy.remove_metadata("codec")
    assert proxy.get_metadata("codec") is None

    proxy.set_metadata("a", 1)
    proxy.clear_metadata()
    assert proxy.metadata == {}


def test_clone_gets_new_id(tmp_path: Path) -> None:
    proxy = _proxy(tmp_path)
    clone = proxy.clone()

    assert clone.id != proxy.id
    assert clone.proxy_path == proxy.proxy_path
