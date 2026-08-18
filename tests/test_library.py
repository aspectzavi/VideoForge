"""
Fast, pytest-based tests for MediaLibrary (media/library.py).
"""

from __future__ import annotations

from pathlib import Path

import pytest

from videoforge.media.library import MediaLibrary

SAMPLE_MEDIA = Path("tests/sample_media/input.mp4")


def test_defaults() -> None:
    library = MediaLibrary()

    assert library.is_empty is True
    assert library.asset_count == 0
    assert len(library) == 0


def test_import_file_adds_asset() -> None:
    library = MediaLibrary()

    asset = library.import_file(SAMPLE_MEDIA)

    assert library.asset_count == 1
    assert library.is_empty is False
    assert library[0] is asset


def test_import_file_deduplicates_by_resolved_path() -> None:
    library = MediaLibrary()

    first = library.import_file(SAMPLE_MEDIA)
    second = library.import_file(SAMPLE_MEDIA)

    assert first is second
    assert library.asset_count == 1


def test_import_files_multiple() -> None:
    library = MediaLibrary()
    assets = library.import_files([SAMPLE_MEDIA])

    assert len(assets) == 1
    assert library.asset_count == 1


def test_remove_and_remove_path() -> None:
    library = MediaLibrary()
    asset = library.import_file(SAMPLE_MEDIA)

    library.remove(asset)
    assert library.is_empty is True

    library.import_file(SAMPLE_MEDIA)
    assert library.remove_path(SAMPLE_MEDIA) is True
    assert library.remove_path(SAMPLE_MEDIA) is False


def test_find_by_path_name_and_id() -> None:
    library = MediaLibrary()
    asset = library.import_file(SAMPLE_MEDIA)

    assert library.find(SAMPLE_MEDIA) is asset
    assert library.find_by_name("input.mp4") is asset
    assert library.find_by_id(asset.id) is asset
    assert library.contains(SAMPLE_MEDIA) is True

    assert library.find("missing.mp4") is None
    assert library.find_by_name("missing.mp4") is None
    assert library.find_by_id("missing-id") is None


def test_reference_and_resolve() -> None:
    library = MediaLibrary()
    asset = library.import_file(SAMPLE_MEDIA)

    ref = library.reference(asset)
    assert ref.asset_id == asset.id

    resolved = library.resolve(ref)
    assert resolved is asset


def test_create_bin_and_collection() -> None:
    library = MediaLibrary()

    bin_ = library.create_bin("Footage")
    collection = library.create_collection("Favorites")

    assert bin_ in library.bins
    assert collection in library.collections
    assert library.bin_count == 1
    assert library.collection_count == 1


def test_filtering_by_type() -> None:
    library = MediaLibrary()
    library.import_file(SAMPLE_MEDIA)

    assert len(library.videos()) == 1
    assert library.audios() == []
    assert library.images() == []
    assert library.gifs() == []
    assert library.video_count == 1
    assert library.audio_count == 0
    assert library.image_count == 0


def test_search() -> None:
    library = MediaLibrary()
    library.import_file(SAMPLE_MEDIA)

    assert len(library.search("input")) == 1
    assert library.search("nonexistent") == []


def test_sorting_does_not_raise() -> None:
    library = MediaLibrary()
    library.import_file(SAMPLE_MEDIA)

    library.sort_by_name()
    library.sort_by_size()
    library.sort_by_duration()  # triggers real ffprobe via asset.duration


def test_total_size() -> None:
    library = MediaLibrary()
    library.import_file(SAMPLE_MEDIA)

    assert library.total_size_bytes > 0
    assert library.total_size_mb == pytest.approx(
        library.total_size_bytes / (1024 * 1024), rel=1e-3
    )


def test_clear() -> None:
    library = MediaLibrary()
    library.import_file(SAMPLE_MEDIA)
    library.create_bin("Footage")
    library.create_collection("Favorites")

    library.clear()

    assert library.is_empty is True
    assert library.bin_count == 0
    assert library.collection_count == 0


def test_summary() -> None:
    library = MediaLibrary()
    library.import_file(SAMPLE_MEDIA)

    summary = library.summary()

    assert summary["assets"] == 1
    assert summary["videos"] == 1
