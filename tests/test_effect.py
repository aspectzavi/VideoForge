"""
Fast, pytest-based tests for the Effect model hierarchy.

No FFmpeg/probing involved anywhere in this file.
"""

from __future__ import annotations

import pytest

from videoforge.media.effect import (
    BlurEffect,
    ChromaKeyEffect,
    ColorEffect,
    CustomEffect,
    Effect,
    EffectType,
    SharpenEffect,
    SpeedEffect,
    VolumeEffect,
)


# ---------------------------------------------------------------------
# Base Effect
# ---------------------------------------------------------------------


def test_effect_defaults() -> None:
    effect = Effect(name="Test")

    assert effect.type == EffectType.CUSTOM
    assert effect.enabled is True
    assert effect.is_enabled is True
    assert effect.start == 0.0
    assert effect.end is None
    assert effect.duration is None


def test_effect_duration_uses_start_and_end() -> None:
    effect = Effect(name="Test", start=2.0, end=7.0)
    assert effect.duration == pytest.approx(5.0)


def test_effect_duration_clamped_at_zero_when_end_before_start() -> None:
    effect = Effect(name="Test", start=10.0, end=4.0)
    assert effect.duration == 0.0


def test_effect_base_ffmpeg_filter_raises_not_implemented() -> None:
    effect = Effect(name="Test")

    with pytest.raises(NotImplementedError):
        effect.ffmpeg_filter()


# ---------------------------------------------------------------------
# Parameter helpers
# ---------------------------------------------------------------------


def test_effect_parameter_helpers() -> None:
    effect = Effect(name="Test")

    assert effect.has("intensity") is False
    assert effect.get("intensity", "default") == "default"

    effect.set("intensity", 5)

    assert effect.has("intensity") is True
    assert effect.get("intensity") == 5

    effect.remove("intensity")

    assert effect.has("intensity") is False

    effect.set("a", 1)
    effect.set("b", 2)
    effect.clear_parameters()

    assert effect.parameters == {}


def test_effect_remove_missing_key_is_a_noop() -> None:
    effect = Effect(name="Test")
    effect.remove("does-not-exist")  # should not raise
    assert effect.parameters == {}


# ---------------------------------------------------------------------
# State toggles
# ---------------------------------------------------------------------


def test_effect_enable_disable_toggle() -> None:
    effect = Effect(name="Test")

    effect.disable()
    assert effect.enabled is False
    assert effect.is_enabled is False

    effect.enable()
    assert effect.enabled is True

    effect.toggle()
    assert effect.enabled is False
    effect.toggle()
    assert effect.enabled is True


# ---------------------------------------------------------------------
# Timing
# ---------------------------------------------------------------------


def test_effect_set_range_and_clear_range() -> None:
    effect = Effect(name="Test")

    effect.set_range(1.0, 5.0)
    assert effect.start == 1.0
    assert effect.end == 5.0

    effect.clear_range()
    assert effect.start == 0.0
    assert effect.end is None


# ---------------------------------------------------------------------
# Cloning / serialization
# ---------------------------------------------------------------------


def test_effect_clone_gets_new_id_and_is_independent() -> None:
    effect = Effect(name="Test")
    effect.set("intensity", 5)

    clone = effect.clone()

    assert clone.id != effect.id
    assert clone.get("intensity") == 5

    clone.set("intensity", 99)

    assert effect.get("intensity") == 5


def test_effect_to_dict_matches_model_dump() -> None:
    effect = Effect(name="Test")
    assert effect.to_dict() == effect.model_dump()


# ---------------------------------------------------------------------
# Subclass ffmpeg_filter() output
# ---------------------------------------------------------------------


def test_blur_effect_filter() -> None:
    effect = BlurEffect(strength=10)
    assert effect.ffmpeg_filter() == "boxblur=10"
    assert effect.type == EffectType.BLUR


def test_sharpen_effect_filter() -> None:
    effect = SharpenEffect(amount=2.0)
    assert effect.ffmpeg_filter() == "unsharp=5:5:2.0:5:5:0"
    assert effect.type == EffectType.SHARPEN


def test_color_effect_filter() -> None:
    effect = ColorEffect(brightness=0.1, contrast=1.2, saturation=0.9, gamma=1.0)
    assert effect.ffmpeg_filter() == "eq=brightness=0.1:contrast=1.2:saturation=0.9:gamma=1.0"
    assert effect.type == EffectType.COLOR


def test_speed_effect_filter() -> None:
    effect = SpeedEffect(multiplier=2.0)
    assert effect.ffmpeg_filter() == "setpts=0.5*PTS"
    assert effect.type == EffectType.SPEED


def test_speed_effect_filter_guards_against_zero_multiplier() -> None:
    effect = SpeedEffect(multiplier=0.0)
    # documented divide-by-zero guard: falls back to factor 1.0
    assert effect.ffmpeg_filter() == "setpts=1.0*PTS"


def test_volume_effect_filter() -> None:
    effect = VolumeEffect(volume=0.5)
    assert effect.ffmpeg_filter() == "volume=0.5"
    assert effect.type == EffectType.AUDIO


def test_chroma_key_effect_filter() -> None:
    effect = ChromaKeyEffect(color="0xFF00FF", similarity=0.3, blend=0.1)
    assert (
        effect.ffmpeg_filter()
        == "chromakey=color=0xFF00FF:similarity=0.3:blend=0.1"
    )
    assert effect.type == EffectType.CHROMA_KEY


def test_custom_effect_filter_passthrough() -> None:
    effect = CustomEffect(filter_expression="hue=s=0")
    assert effect.ffmpeg_filter() == "hue=s=0"
    assert effect.type == EffectType.CUSTOM


def test_custom_effect_requires_filter_expression() -> None:
    with pytest.raises(Exception):
        CustomEffect()  # missing required field
