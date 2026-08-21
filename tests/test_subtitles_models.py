"""
Fast, pytest-based tests for subtitles/subtitles.py.

These are in-memory subtitle models (SubtitleCue/Track/Style/Document)
distinct from operations/subtitles/, which works directly with
file-based .srt/.vtt conversion via FFmpeg. Confirmed via a full-repo
search that nothing else references these models - a standalone,
currently-unwired capability (likely intended for programmatically
building captions, e.g. from AI transcription, before writing to
disk).
"""

from __future__ import annotations

import pytest

from videoforge.subtitles.subtitles import (
    SubtitleCue,
    SubtitleDocument,
    SubtitleFormat,
    SubtitleStyle,
    SubtitleTrack,
)


def test_subtitle_cue_duration() -> None:
    cue = SubtitleCue(start=1.0, end=4.0, text="Hello")
    assert cue.duration == pytest.approx(3.0)


def test_subtitle_cue_duration_clamped_at_zero() -> None:
    cue = SubtitleCue(start=5.0, end=2.0, text="Bad range")
    assert cue.duration == 0.0


def test_subtitle_cue_optional_fields() -> None:
    cue = SubtitleCue(start=0.0, end=1.0, text="Hi")
    assert cue.speaker is None
    assert cue.confidence is None
    assert cue.words == []


def test_subtitle_track_defaults() -> None:
    track = SubtitleTrack()

    assert track.language == "en"
    assert track.format == SubtitleFormat.SRT
    assert track.default is True
    assert track.forced is False
    assert track.cue_count == 0
    assert track.duration == 0.0


def test_subtitle_track_add_and_clear() -> None:
    track = SubtitleTrack()
    track.add(SubtitleCue(start=0.0, end=2.0, text="Hi"))

    assert track.cue_count == 1

    track.clear()
    assert track.cue_count == 0


def test_subtitle_track_sort_orders_by_start() -> None:
    track = SubtitleTrack()
    track.add(SubtitleCue(start=10.0, end=15.0, text="second"))
    track.add(SubtitleCue(start=0.0, end=5.0, text="first"))

    track.sort()

    assert [cue.text for cue in track.cues] == ["first", "second"]


def test_subtitle_track_duration_requires_sorted_cues() -> None:
    """
    Documents a real quirk rather than an idealized behavior:
    SubtitleTrack.duration reads cues[-1].end (the LAST cue in list
    order), not max(cue.end for cue in cues). add() does not
    auto-sort, so adding cues out of chronological order gives a
    wrong (too-short) duration until sort() is called explicitly.
    """
    track = SubtitleTrack()
    track.add(SubtitleCue(start=10.0, end=15.0, text="second"))
    track.add(SubtitleCue(start=0.0, end=5.0, text="first"))

    assert track.duration == pytest.approx(5.0)  # wrong: should be 15.0

    track.sort()

    assert track.duration == pytest.approx(15.0)  # correct once sorted


def test_subtitle_style_defaults() -> None:
    style = SubtitleStyle()

    assert style.font == "Arial"
    assert style.font_size == 36
    assert style.bold is False
    assert style.alignment == 2


def test_subtitle_document_defaults() -> None:
    track = SubtitleTrack()
    doc = SubtitleDocument(track=track)

    assert doc.track is track
    assert isinstance(doc.style, SubtitleStyle)
    assert doc.metadata == {}


def test_subtitle_document_with_custom_style_and_metadata() -> None:
    track = SubtitleTrack()
    style = SubtitleStyle(font="Helvetica", bold=True)
    doc = SubtitleDocument(track=track, style=style, metadata={"source": "whisper"})

    assert doc.style.font == "Helvetica"
    assert doc.style.bold is True
    assert doc.metadata["source"] == "whisper"


@pytest.mark.parametrize(
    "fmt", [SubtitleFormat.SRT, SubtitleFormat.VTT, SubtitleFormat.ASS, SubtitleFormat.SSA]
)
def test_subtitle_format_values(fmt: SubtitleFormat) -> None:
    track = SubtitleTrack(format=fmt)
    assert track.format == fmt
