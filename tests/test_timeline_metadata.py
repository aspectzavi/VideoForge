"""
Fast, pytest-based tests for TimelineMetadata (media/timeline_metadata.py).
"""

from __future__ import annotations

from videoforge.engine.version import VERSION
from videoforge.media.timeline_metadata import TimelineMetadata


def test_defaults() -> None:
    meta = TimelineMetadata()

    assert meta.name == "Untitled Timeline"
    assert meta.description is None
    assert meta.author is None
    assert meta.version == VERSION
    assert meta.has_description is False
    assert meta.has_author is False


def test_rename_updates_name_and_touches() -> None:
    meta = TimelineMetadata()
    original_modified = meta.modified_at

    meta.rename("My Edit")

    assert meta.name == "My Edit"
    assert meta.modified_at >= original_modified


def test_update_description() -> None:
    meta = TimelineMetadata()

    meta.update_description("A short film")

    assert meta.description == "A short film"
    assert meta.has_description is True


def test_update_author() -> None:
    meta = TimelineMetadata()

    meta.update_author("Kevin")

    assert meta.author == "Kevin"
    assert meta.has_author is True


def test_str_returns_name() -> None:
    meta = TimelineMetadata(name="Sequence 01")
    assert str(meta) == "Sequence 01"
