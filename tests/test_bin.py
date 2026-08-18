"""
Fast, pytest-based tests for MediaBin (media/bin.py).
"""

from __future__ import annotations

from videoforge.media.bin import MediaBin


def test_defaults() -> None:
    bin_ = MediaBin(name="Footage")

    assert bin_.bin_type == "folder"
    assert bin_.is_root is True
    assert bin_.is_empty is True
    assert bin_.asset_count == 0
    assert bin_.child_count == 0


def test_add_and_remove_assets() -> None:
    bin_ = MediaBin(name="Footage")

    bin_.add_asset("a1")
    bin_.add_asset("a1")  # duplicate, ignored
    bin_.add_assets(["a2", "a3"])

    assert bin_.asset_count == 3
    assert bin_.contains("a1") is True
    assert bin_.is_empty is False

    assert bin_.remove_asset("a1") is True
    assert bin_.remove_asset("missing") is False
    assert bin_.asset_count == 2

    bin_.clear_assets()
    assert bin_.is_empty is True


def test_child_bins() -> None:
    bin_ = MediaBin(name="Root")

    bin_.add_child("child-1")
    bin_.add_child("child-1")  # duplicate, ignored
    assert bin_.child_count == 1

    assert bin_.remove_child("child-1") is True
    assert bin_.remove_child("missing") is False
    assert bin_.child_count == 0


def test_is_root_false_when_has_parent() -> None:
    bin_ = MediaBin(name="Child", parent_id="parent-1")
    assert bin_.is_root is False


def test_all_bin_ids_includes_self_and_children() -> None:
    bin_ = MediaBin(name="Root")
    bin_.add_child("c1")
    bin_.add_child("c2")

    assert bin_.all_bin_ids() == [bin_.id, "c1", "c2"]


def test_sort_assets() -> None:
    bin_ = MediaBin(name="Footage")
    bin_.add_assets(["c", "a", "b"])

    bin_.sort_assets()

    assert bin_.asset_ids == ["a", "b", "c"]


def test_rename() -> None:
    bin_ = MediaBin(name="Old")
    bin_.rename("New")
    assert bin_.name == "New"


def test_clone_gets_new_id() -> None:
    bin_ = MediaBin(name="Footage")
    bin_.add_asset("a1")

    clone = bin_.clone()

    assert clone.id != bin_.id
    assert clone.asset_ids == ["a1"]


def test_str_and_repr() -> None:
    bin_ = MediaBin(name="Footage")
    assert str(bin_) == "Footage"
    assert "MediaBin" in repr(bin_)
