"""
Fast, pytest-based tests for Overlay (media/overlay.py).
"""

from __future__ import annotations

import pytest

from videoforge.media.asset_reference import AssetReference
from videoforge.media.overlay import Overlay, OverlayType, TextStyle


def test_defaults() -> None:
    overlay = Overlay()

    assert overlay.type == OverlayType.IMAGE
    assert overlay.enabled is True
    assert overlay.duration == 0.0
    assert overlay.is_visible is False  # duration is 0
    assert overlay.has_asset is False
    assert overlay.asset_id is None
    assert overlay.is_text is False


def test_set_range_and_duration() -> None:
    overlay = Overlay()

    overlay.set_range(5.0, 15.0)
    assert overlay.duration == pytest.approx(10.0)
    assert overlay.is_visible is True

    overlay.set_duration(3.0)
    assert overlay.end == pytest.approx(8.0)  # start(5) + 3


def test_set_range_clamps_end_to_start() -> None:
    overlay = Overlay()
    overlay.set_range(10.0, 5.0)

    assert overlay.end == 10.0  # clamped, never before start


def test_contains() -> None:
    overlay = Overlay()
    overlay.set_range(5.0, 10.0)

    assert overlay.contains(5.0) is True
    assert overlay.contains(9.9) is True
    assert overlay.contains(10.0) is False  # end is exclusive
    assert overlay.contains(4.9) is False


def test_transform_helpers() -> None:
    overlay = Overlay()

    overlay.set_position(0.2, 0.3)
    assert (overlay.x, overlay.y) == (0.2, 0.3)

    overlay.move(0.1, -0.1)
    assert overlay.x == pytest.approx(0.3)
    assert overlay.y == pytest.approx(0.2)

    overlay.set_scale(2.0)
    assert (overlay.scale_x, overlay.scale_y) == (2.0, 2.0)

    overlay.resize(1.5)
    assert overlay.scale_x == pytest.approx(3.0)
    assert overlay.scale_y == pytest.approx(3.0)


def test_set_opacity_is_clamped() -> None:
    overlay = Overlay()

    overlay.set_opacity(1.5)
    assert overlay.opacity == 1.0

    overlay.set_opacity(-0.5)
    assert overlay.opacity == 0.0


def test_asset_reference() -> None:
    overlay = Overlay()
    ref = AssetReference(asset_id="a1")

    overlay.set_asset_reference(ref)
    assert overlay.has_asset is True
    assert overlay.asset_id == "a1"

    overlay.clear_asset()
    assert overlay.has_asset is False
    assert overlay.asset_id is None


def test_text() -> None:
    overlay = Overlay(type=OverlayType.TEXT)
    assert overlay.is_text is True

    overlay.set_text("Hello")
    assert overlay.text == "Hello"

    style = TextStyle(size=72, bold=True)
    overlay.set_text_style(style)
    assert overlay.text_style.size == 72
    assert overlay.text_style.bold is True


def test_keyframes() -> None:
    overlay = Overlay()

    overlay.add_keyframe("opacity", 5.0, 1.0)
    overlay.add_keyframe("opacity", 0.0, 0.0)

    assert [kf.time for kf in overlay.keyframes["opacity"]] == [0.0, 5.0]

    overlay.add_keyframe("x", 0.0, 0.5)
    overlay.clear_keyframes("opacity")
    assert "opacity" not in overlay.keyframes
    assert "x" in overlay.keyframes

    overlay.clear_keyframes()
    assert overlay.keyframes == {}


def test_state_toggles() -> None:
    overlay = Overlay()

    overlay.disable()
    assert overlay.enabled is False
    overlay.enable()
    assert overlay.enabled is True
    overlay.toggle()
    assert overlay.enabled is False

    overlay.lock()
    assert overlay.locked is True
    overlay.unlock()
    assert overlay.locked is False

    overlay.select()
    assert overlay.selected is True
    overlay.deselect()
    assert overlay.selected is False


def test_tags_and_metadata() -> None:
    overlay = Overlay()

    overlay.add_tag("logo")
    overlay.add_tag("logo")
    assert overlay.tags == ["logo"]
    assert overlay.remove_tag("logo") is True
    assert overlay.remove_tag("logo") is False

    overlay.add_tag("a")
    overlay.clear_tags()
    assert overlay.tags == []

    overlay.set_metadata("k", "v")
    assert overlay.get_metadata("k") == "v"
    overlay.remove_metadata("k")
    assert overlay.get_metadata("k") is None


def test_clone_gets_new_id_and_is_independent() -> None:
    overlay = Overlay()
    overlay.set_text("Original")

    clone = overlay.clone()

    assert clone.id != overlay.id

    clone.set_text("Changed")
    assert overlay.text == "Original"


def test_to_dict_matches_model_dump() -> None:
    overlay = Overlay()
    assert overlay.to_dict() == overlay.model_dump()


def test_str_and_repr() -> None:
    overlay = Overlay(name="Logo Overlay")
    assert str(overlay) == "Logo Overlay"
    assert "Overlay" in repr(overlay)
