"""
Fast, pytest-based tests for AssetReference (media/asset_reference.py).
"""

from __future__ import annotations

from videoforge.media.asset_reference import AssetReference


def test_defaults() -> None:
    ref = AssetReference(asset_id="asset-1")

    assert ref.name is None
    assert ref.favorite is False
    assert ref.enabled is True
    assert ref.offline is False
    assert ref.rating == 0
    assert ref.has_notes is False
    assert ref.is_rated is False
    assert ref.is_disabled is False
    assert ref.is_offline is False
    assert ref.reference_key == f"asset-1:{ref.id}"


def test_tags() -> None:
    ref = AssetReference(asset_id="a")

    ref.add_tag("b-roll")
    ref.add_tag("b-roll")  # duplicate, ignored
    ref.add_tag("drone")

    assert ref.tags == ["b-roll", "drone"]

    assert ref.remove_tag("b-roll") is True
    assert ref.remove_tag("missing") is False
    assert ref.tags == ["drone"]

    ref.clear_tags()
    assert ref.tags == []
    assert ref.has_tag("drone") is False


def test_rating_is_clamped() -> None:
    ref = AssetReference(asset_id="a")

    ref.set_rating(10)
    assert ref.rating == 5
    assert ref.is_rated is True

    ref.set_rating(-5)
    assert ref.rating == 0

    ref.set_rating(3)
    ref.clear_rating()
    assert ref.rating == 0


def test_state_toggles() -> None:
    ref = AssetReference(asset_id="a")

    ref.disable()
    assert ref.enabled is False
    assert ref.is_disabled is True

    ref.enable()
    assert ref.enabled is True

    ref.toggle()
    assert ref.enabled is False

    ref.mark_favorite()
    assert ref.favorite is True
    ref.unmark_favorite()
    assert ref.favorite is False
    ref.toggle_favorite()
    assert ref.favorite is True

    ref.mark_offline()
    assert ref.offline is True
    assert ref.is_offline is True
    ref.mark_online()
    assert ref.offline is False


def test_metadata() -> None:
    ref = AssetReference(asset_id="a")

    ref.set_metadata("key", "value")
    assert ref.get_metadata("key") == "value"
    assert ref.get_metadata("missing", "default") == "default"

    ref.remove_metadata("key")
    assert ref.get_metadata("key") is None

    ref.set_metadata("a", 1)
    ref.set_metadata("b", 2)
    ref.clear_metadata()
    assert ref.metadata == {}


def test_utilities() -> None:
    ref = AssetReference(asset_id="a")

    ref.rename("Clip A")
    assert ref.name == "Clip A"

    ref.set_label("Hero Shot")
    assert ref.label == "Hero Shot"

    ref.set_notes("Great take")
    assert ref.notes == "Great take"
    assert ref.has_notes is True

    ref.increment_usage()
    ref.increment_usage()
    assert ref.usage_count == 2

    ref.reset_usage()
    assert ref.usage_count == 0


def test_clone_gets_new_id_and_is_independent() -> None:
    ref = AssetReference(asset_id="a")
    ref.add_tag("original")

    clone = ref.clone()

    assert clone.id != ref.id
    assert clone.asset_id == ref.asset_id

    clone.add_tag("clone-only")
    assert "clone-only" not in ref.tags


def test_str_and_repr() -> None:
    ref = AssetReference(asset_id="a")
    assert str(ref) == "a"  # falls back to asset_id when name is None

    ref.rename("Named")
    assert str(ref) == "Named"

    assert "AssetReference" in repr(ref)
