"""
Fast, pytest-based tests for MediaCollection (media/collection.py).
"""

from __future__ import annotations

from videoforge.media.collection import (
    CollectionRule,
    CollectionType,
    MediaCollection,
)


def test_defaults() -> None:
    collection = MediaCollection(name="Favorites")

    assert collection.type == CollectionType.MANUAL
    assert collection.is_manual is True
    assert collection.is_smart is False
    assert collection.is_temporary is False
    assert collection.is_empty is True
    assert collection.asset_count == 0


def test_add_and_remove_assets() -> None:
    collection = MediaCollection(name="Favorites")

    collection.add_asset("a1")
    collection.add_asset("a1")  # duplicate, ignored
    collection.add_assets(["a2", "a3"])

    assert collection.asset_count == 3
    assert collection.contains("a1") is True
    assert "a2" in collection  # __contains__
    assert len(collection) == 3  # __len__

    assert collection.remove_asset("a1") is True
    assert collection.remove_asset("missing") is False
    assert collection.asset_count == 2

    collection.clear_assets()
    assert collection.is_empty is True


def test_smart_collection_rules() -> None:
    collection = MediaCollection(name="Long Videos", type=CollectionType.SMART)
    rule = CollectionRule(field="duration", operator=">", value=60)

    collection.add_rule(rule)
    assert len(collection.rules) == 1
    assert collection.is_smart is True

    assert collection.remove_rule(rule) is True
    assert collection.remove_rule(rule) is False
    assert collection.rules == []

    collection.add_rule(rule)
    collection.clear_rules()
    assert collection.rules == []


def test_tags() -> None:
    collection = MediaCollection(name="Favorites")

    collection.add_tag("a")
    collection.add_tag("a")
    assert collection.tags == ["a"]

    assert collection.remove_tag("a") is True
    assert collection.remove_tag("a") is False

    collection.add_tag("b")
    collection.clear_tags()
    assert collection.tags == []


def test_rename_and_metadata_setters() -> None:
    collection = MediaCollection(name="Old")

    collection.rename("New")
    assert collection.name == "New"

    collection.set_color("#FF0000")
    assert collection.color == "#FF0000"

    collection.set_description("A collection")
    assert collection.description == "A collection"


def test_clear_clears_assets_and_rules() -> None:
    collection = MediaCollection(name="Favorites")
    collection.add_asset("a1")
    collection.add_rule(CollectionRule(field="x", operator="==", value=1))

    collection.clear()

    assert collection.asset_ids == []
    assert collection.rules == []


def test_clone_gets_new_id() -> None:
    collection = MediaCollection(name="Favorites")
    collection.add_asset("a1")

    clone = collection.clone()

    assert clone.id != collection.id
    assert clone.asset_ids == ["a1"]


def test_str_and_repr() -> None:
    collection = MediaCollection(name="Favorites")
    assert str(collection) == "Favorites"
    assert "MediaCollection" in repr(collection)
