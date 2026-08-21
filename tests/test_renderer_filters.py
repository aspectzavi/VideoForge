"""
Fast, pytest-based tests for renderer/filters.py.
"""

from __future__ import annotations

import pytest

from videoforge.renderer.filters import (
    AudioFadeFilter,
    AudioTempoFilter,
    BlurFilter,
    CropFilter,
    CustomFilter,
    DrawTextFilter,
    FilterChain,
    FlipFilter,
    FPSFilter,
    OverlayFilter,
    PadFilter,
    RotateFilter,
    ScaleFilter,
    SetPTSFilter,
    TrimFilter,
    VolumeFilter,
    build_filter_chain,
)


def test_scale_filter() -> None:
    assert ScaleFilter(width=1080, height=1920).to_ffmpeg() == "scale=1080:1920"


def test_scale_filter_with_flags() -> None:
    f = ScaleFilter(width=1080, height=1920, flags="lanczos")
    assert f.to_ffmpeg() == "scale=1080:1920:flags=lanczos"


def test_crop_filter_defaults_center() -> None:
    f = CropFilter(width=100, height=100)
    assert f.to_ffmpeg() == "crop=100:100:(iw-ow)/2:(ih-oh)/2"


def test_pad_filter_defaults() -> None:
    f = PadFilter(width=1920, height=1080)
    assert f.to_ffmpeg() == "pad=1920:1080:(ow-iw)/2:(oh-ih)/2:black"


def test_blur_filter_defaults() -> None:
    assert BlurFilter().to_ffmpeg() == "boxblur=20:5"


def test_rotate_filter() -> None:
    f = RotateFilter(angle=1.57)
    assert f.to_ffmpeg() == "rotate=1.57:fillcolor=black"


@pytest.mark.parametrize(
    "horizontal,vertical,expected",
    [
        (True, False, "hflip"),
        (False, True, "vflip"),
        (True, True, "hflip,vflip"),
        (False, False, ""),
    ],
)
def test_flip_filter(horizontal: bool, vertical: bool, expected: str) -> None:
    f = FlipFilter(horizontal=horizontal, vertical=vertical)
    assert f.to_ffmpeg() == expected


def test_fps_filter() -> None:
    assert FPSFilter(fps=24.0).to_ffmpeg() == "fps=24.0"


def test_trim_filter_all_fields() -> None:
    f = TrimFilter(start=1.0, end=5.0, duration=4.0)
    assert f.to_ffmpeg() == "trim=start=1.0:end=5.0:duration=4.0"


def test_trim_filter_partial_fields() -> None:
    f = TrimFilter(start=1.0)
    assert f.to_ffmpeg() == "trim=start=1.0"


def test_setpts_filter_default() -> None:
    assert SetPTSFilter().to_ffmpeg() == "setpts=PTS-STARTPTS"


def test_draw_text_filter_basic() -> None:
    f = DrawTextFilter(text="Hello")
    result = f.to_ffmpeg()

    assert result.startswith("drawtext=")
    assert "text='Hello'" in result
    assert "fontsize=48" in result
    assert "borderw" not in result


def test_draw_text_filter_with_border_and_font_file() -> None:
    f = DrawTextFilter(
        text="Hi", border_width=2, border_color="red", font_file="arial.ttf"
    )
    result = f.to_ffmpeg()

    assert "borderw=2" in result
    assert "bordercolor=red" in result
    assert "fontfile=arial.ttf" in result


def test_overlay_filter_defaults() -> None:
    f = OverlayFilter()
    assert f.to_ffmpeg() == "overlay=(W-w)/2:(H-h)/2:shortest=1:eof_action=repeat"


def test_overlay_filter_without_shortest() -> None:
    f = OverlayFilter(shortest=False)
    assert f.to_ffmpeg() == "overlay=(W-w)/2:(H-h)/2:eof_action=repeat"


def test_volume_filter() -> None:
    assert VolumeFilter(volume=0.5).to_ffmpeg() == "volume=0.5"


def test_audio_fade_filter() -> None:
    f = AudioFadeFilter(fade_type="out", start=10.0, duration=2.0)
    assert f.to_ffmpeg() == "afade=t=out:st=10.0:d=2.0"


def test_audio_tempo_filter() -> None:
    assert AudioTempoFilter(tempo=1.5).to_ffmpeg() == "atempo=1.5"


def test_custom_filter_passthrough() -> None:
    assert CustomFilter(expression="hue=s=0").to_ffmpeg() == "hue=s=0"


def test_filter_disabled_is_falsy_string() -> None:
    f = ScaleFilter(width=100, height=100, enabled=False)

    # to_ffmpeg() itself doesn't check `enabled` - that's FilterChain's
    # job (see test_filter_chain_skips_disabled_filters below).
    assert f.to_ffmpeg() == "scale=100:100"
    assert f.enabled is False


# ---------------------------------------------------------------------
# FilterChain
# ---------------------------------------------------------------------


def test_filter_chain_joins_with_commas() -> None:
    chain = FilterChain()
    chain.add(ScaleFilter(width=100, height=100), FlipFilter(horizontal=True))

    assert chain.to_ffmpeg() == "scale=100:100,hflip"
    assert len(chain) == 2
    assert chain[0].to_ffmpeg() == "scale=100:100"


def test_filter_chain_skips_disabled_filters() -> None:
    chain = FilterChain()
    chain.add(
        ScaleFilter(width=100, height=100),
        FlipFilter(horizontal=True, enabled=False),
    )

    assert chain.to_ffmpeg() == "scale=100:100"


def test_filter_chain_skips_empty_output() -> None:
    # FlipFilter with neither horizontal nor vertical produces "" -
    # FilterChain must skip it, not join a stray empty segment.
    chain = FilterChain()
    chain.add(ScaleFilter(width=100, height=100), FlipFilter())

    assert chain.to_ffmpeg() == "scale=100:100"


def test_filter_chain_extend_and_clear() -> None:
    chain = FilterChain()
    chain.extend([ScaleFilter(width=100, height=100)])
    assert len(chain) == 1

    chain.clear()
    assert len(chain) == 0


def test_filter_chain_str() -> None:
    chain = FilterChain()
    chain.add(ScaleFilter(width=100, height=100))
    assert str(chain) == "scale=100:100"


def test_build_filter_chain_helper() -> None:
    result = build_filter_chain(
        ScaleFilter(width=1080, height=1920),
        CropFilter(width=1080, height=1920),
    )

    assert result == "scale=1080:1920,crop=1080:1920:(iw-ow)/2:(ih-oh)/2"
