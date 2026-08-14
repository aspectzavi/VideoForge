"""
Fast, pytest-based tests for Transition.
"""

from __future__ import annotations

import pytest

from videoforge.media.transition import (
    Transition,
    TransitionEasing,
    TransitionType,
)


# ---------------------------------------------------------------------
# Defaults / computed properties
# ---------------------------------------------------------------------


def test_transition_defaults() -> None:
    t = Transition()

    assert t.type == TransitionType.CROSSFADE
    assert t.duration == 1.0
    assert t.offset == 0.0
    assert t.easing == TransitionEasing.LINEAR
    assert t.enabled is True
    assert t.is_crossfade is True
    assert t.is_cut is False


def test_transition_is_cut_when_type_is_cut() -> None:
    t = Transition(type=TransitionType.CUT)
    assert t.is_cut is True


def test_transition_is_cut_when_duration_is_zero_or_less() -> None:
    t = Transition(type=TransitionType.FADE, duration=0.0)
    assert t.is_cut is True

    t2 = Transition(type=TransitionType.FADE, duration=-1.0)
    assert t2.is_cut is True


@pytest.mark.parametrize(
    "transition_type",
    [TransitionType.CROSSFADE, TransitionType.DISSOLVE, TransitionType.FADE],
)
def test_transition_is_crossfade_for_fade_family(
    transition_type: TransitionType,
) -> None:
    t = Transition(type=transition_type)
    assert t.is_crossfade is True


def test_transition_is_crossfade_false_for_wipe() -> None:
    t = Transition(type=TransitionType.WIPE_LEFT)
    assert t.is_crossfade is False


@pytest.mark.parametrize(
    "transition_type,expected_name",
    [
        (TransitionType.CUT, "fade"),
        (TransitionType.FADE, "fade"),
        (TransitionType.DISSOLVE, "fade"),
        (TransitionType.CROSSFADE, "fade"),
        (TransitionType.WIPE_LEFT, "wipeleft"),
        (TransitionType.WIPE_RIGHT, "wiperight"),
        (TransitionType.SLIDE_UP, "slideup"),
        (TransitionType.ZOOM_IN, "zoomin"),
        (TransitionType.CIRCLE_OPEN, "circleopen"),
        (TransitionType.PIXELIZE, "pixelize"),
        (TransitionType.BLUR, "fade"),
        # unmapped custom type falls back to "fade"
        (TransitionType.CUSTOM, "fade"),
    ],
)
def test_transition_ffmpeg_name_mapping(
    transition_type: TransitionType, expected_name: str
) -> None:
    t = Transition(type=transition_type)
    assert t.ffmpeg_name == expected_name


# ---------------------------------------------------------------------
# Parameters
# ---------------------------------------------------------------------


def test_transition_parameter_helpers() -> None:
    t = Transition()

    assert t.get_parameter("angle", 0) == 0

    t.set_parameter("angle", 45)

    assert t.get_parameter("angle") == 45


# ---------------------------------------------------------------------
# enable / disable
# ---------------------------------------------------------------------


def test_transition_enable_disable() -> None:
    t = Transition()

    t.disable()
    assert t.enabled is False

    t.enable()
    assert t.enabled is True


# ---------------------------------------------------------------------
# copy_transition
# ---------------------------------------------------------------------


def test_transition_copy_transition_gets_new_id_and_is_independent() -> None:
    t = Transition(type=TransitionType.WIPE_LEFT)
    t.set_parameter("angle", 45)

    copy = t.copy_transition()

    assert copy.id != t.id
    assert copy.type == TransitionType.WIPE_LEFT
    assert copy.get_parameter("angle") == 45

    copy.set_parameter("angle", 90)

    assert t.get_parameter("angle") == 45


# ---------------------------------------------------------------------
# ffmpeg_arguments
# ---------------------------------------------------------------------


def test_transition_ffmpeg_arguments_basic() -> None:
    t = Transition(type=TransitionType.FADE, duration=2.0)

    args = t.ffmpeg_arguments(offset=5.0)

    assert args == "transition=fade:duration=2.0:offset=5.0"


def test_transition_ffmpeg_arguments_includes_extra_parameters() -> None:
    t = Transition(type=TransitionType.WIPE_LEFT, duration=1.5)
    t.set_parameter("angle", 45)

    args = t.ffmpeg_arguments(offset=3.0)

    assert args == "transition=wipeleft:duration=1.5:offset=3.0:angle=45"
