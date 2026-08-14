"""
Fast, pytest-based tests for Marker.
"""

from __future__ import annotations

import pytest

from videoforge.media.marker import Marker, MarkerColor, MarkerType


# ---------------------------------------------------------------------
# Defaults / computed properties
# ---------------------------------------------------------------------


def test_marker_defaults() -> None:
    marker = Marker()

    assert marker.name == "Marker"
    assert marker.time == 0.0
    assert marker.duration == 0.0
    assert marker.color == MarkerColor.YELLOW
    assert marker.type == MarkerType.STANDARD
    assert marker.enabled is True
    assert marker.is_point is True
    assert marker.is_range is False
    assert marker.end == 0.0
    assert marker.has_comment is False


def test_marker_range_computed_properties() -> None:
    marker = Marker(time=5.0, duration=3.0)

    assert marker.is_range is True
    assert marker.is_point is False
    assert marker.end == pytest.approx(8.0)


def test_marker_has_comment() -> None:
    assert Marker(comment=None).has_comment is False
    assert Marker(comment="").has_comment is False
    assert Marker(comment="a note").has_comment is True


# ---------------------------------------------------------------------
# move / shift
# ---------------------------------------------------------------------


def test_marker_move_sets_absolute_time() -> None:
    marker = Marker(time=5.0)
    marker.move(20.0)
    assert marker.time == pytest.approx(20.0)


def test_marker_move_clamps_at_zero() -> None:
    marker = Marker(time=5.0)
    marker.move(-100.0)
    assert marker.time == pytest.approx(0.0)


def test_marker_shift_is_relative_and_clamps_at_zero() -> None:
    marker = Marker(time=5.0)
    marker.shift(2.0)
    assert marker.time == pytest.approx(7.0)

    marker.shift(-1000.0)
    assert marker.time == pytest.approx(0.0)


# ---------------------------------------------------------------------
# rename / tags
# ---------------------------------------------------------------------


def test_marker_rename() -> None:
    marker = Marker(name="Old")
    marker.rename("New")
    assert marker.name == "New"


def test_marker_add_and_remove_tag() -> None:
    marker = Marker()

    marker.add_tag("chapter-1")
    marker.add_tag("chapter-1")  # duplicate, ignored
    marker.add_tag("intro")

    assert marker.tags == ["chapter-1", "intro"]

    marker.remove_tag("chapter-1")
    marker.remove_tag("not-there")  # no-op, no raise

    assert marker.tags == ["intro"]


# ---------------------------------------------------------------------
# contains()
# ---------------------------------------------------------------------


def test_marker_contains_point_marker() -> None:
    marker = Marker(time=10.0)

    assert marker.contains(10.0) is True
    assert marker.contains(10.0000001) is True  # within epsilon
    assert marker.contains(10.5) is False
    assert marker.contains(9.5) is False


def test_marker_contains_range_marker() -> None:
    marker = Marker(time=10.0, duration=5.0)  # spans 10..15

    assert marker.contains(10.0) is True
    assert marker.contains(12.0) is True
    assert marker.contains(15.0) is True
    assert marker.contains(9.9) is False
    assert marker.contains(15.1) is False


# ---------------------------------------------------------------------
# overlaps()
# ---------------------------------------------------------------------


def test_marker_overlaps_point_marker() -> None:
    marker = Marker(time=10.0)

    assert marker.overlaps(5.0, 15.0) is True
    assert marker.overlaps(10.0, 10.0) is True
    assert marker.overlaps(11.0, 15.0) is False


def test_marker_overlaps_range_marker() -> None:
    marker = Marker(time=10.0, duration=5.0)  # spans 10..15

    assert marker.overlaps(0.0, 10.0) is True  # touches start
    assert marker.overlaps(15.0, 20.0) is True  # touches end
    assert marker.overlaps(11.0, 12.0) is True  # fully inside
    assert marker.overlaps(0.0, 5.0) is False  # entirely before
    assert marker.overlaps(20.0, 25.0) is False  # entirely after


# ---------------------------------------------------------------------
# copy_marker
# ---------------------------------------------------------------------


def test_marker_copy_marker_gets_new_id_and_is_independent() -> None:
    marker = Marker(name="Original")
    marker.add_tag("a")

    copy = marker.copy_marker()

    assert copy.id != marker.id
    assert copy.name == "Original"
    assert copy.tags == ["a"]

    copy.add_tag("b")

    assert "b" not in marker.tags
