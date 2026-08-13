from pathlib import Path

import pytest

from videoforge.media.asset import MediaAsset
from videoforge.media.clip import Clip
from videoforge.media.timeline import Timeline
from videoforge.media.track import Track, TrackType


SAMPLE_MEDIA = Path("tests/sample_media/input.mp4")


@pytest.fixture
def asset() -> MediaAsset:
    """Load the sample media used by timeline tests."""
    return MediaAsset.load(SAMPLE_MEDIA)


@pytest.fixture
def timeline(asset: MediaAsset) -> Timeline:
    """Create a timeline containing two video clips."""
    timeline = Timeline()
    timeline.metadata.name = "Demo Timeline"

    video = Track(
        name="Video",
        type=TrackType.VIDEO,
    )

    audio = Track(
        name="Audio",
        type=TrackType.AUDIO,
    )

    timeline.add_track(video)
    timeline.add_track(audio)

    clip1 = Clip(asset=asset)
    clip1.trim(0, 15)
    clip1.move(0)

    clip2 = Clip(asset=asset)
    clip2.trim(20, 35)
    clip2.move(20)

    video.add_clip(clip1)
    video.add_clip(clip2)

    return timeline


def test_timeline_creation(timeline: Timeline) -> None:
    """Timeline should contain the expected tracks and clips."""

    assert timeline.metadata.name == "Demo Timeline"
    assert timeline.track_count == 2
    assert timeline.clip_count == 2


def test_timeline_duration(timeline: Timeline) -> None:
    """Timeline duration should equal the end of the final clip."""

    assert timeline.duration == pytest.approx(35.0)


def test_timeline_track_types(timeline: Timeline) -> None:
    """Timeline should expose video and audio tracks correctly."""

    assert len(timeline.video_tracks) == 1
    assert len(timeline.audio_tracks) == 1

    assert timeline.video_tracks[0].name == "Video"
    assert timeline.audio_tracks[0].name == "Audio"


def test_timeline_iter_clips(timeline: Timeline) -> None:
    """iter_clips should return clips in timeline order."""

    clips = list(timeline.iter_clips())

    assert len(clips) == 2

    assert clips[0].timeline_start == pytest.approx(0.0)
    assert clips[0].timeline_end == pytest.approx(15.0)

    assert clips[1].timeline_start == pytest.approx(20.0)
    assert clips[1].timeline_end == pytest.approx(35.0)


def test_timeline_clips_at(timeline: Timeline) -> None:
    """clips_at should return the clip occupying a given timeline position."""

    clips_at_10 = timeline.clips_at(10)
    clips_at_25 = timeline.clips_at(25)
    clips_at_17 = timeline.clips_at(17)

    assert len(clips_at_10) == 1
    assert len(clips_at_25) == 1
    assert len(clips_at_17) == 0

    assert clips_at_10[0].timeline_start == pytest.approx(0.0)
    assert clips_at_25[0].timeline_start == pytest.approx(20.0)


def test_timeline_flatten(timeline: Timeline) -> None:
    """flatten should return all timeline clips."""

    flattened = timeline.flatten()

    assert len(flattened) == 2
    assert flattened[0].timeline_start == pytest.approx(0.0)
    assert flattened[1].timeline_start == pytest.approx(20.0)


def test_timeline_ripple(timeline: Timeline) -> None:
    """Ripple should move clips at or after the specified position."""

    timeline.ripple(20, 5)

    clips = list(timeline.iter_clips())

    assert len(clips) == 2

    # First clip remains unchanged.
    assert clips[0].timeline_start == pytest.approx(0.0)
    assert clips[0].timeline_end == pytest.approx(15.0)

    # Second clip moves forward by five seconds.
    assert clips[1].timeline_start == pytest.approx(25.0)
    assert clips[1].timeline_end == pytest.approx(40.0)

    assert timeline.duration == pytest.approx(40.0)


def test_timeline_add_and_remove_track() -> None:
    """Tracks can be added and removed."""

    timeline = Timeline()

    track = Track(
        name="Video",
        type=TrackType.VIDEO,
    )

    timeline.add_track(track)

    assert timeline.track_count == 1
    assert timeline.get_track(track.id) is track

    timeline.remove_track(track)

    assert timeline.track_count == 0
    assert timeline.get_track(track.id) is None


def test_timeline_new_track() -> None:
    """new_track should create and register a track."""

    timeline = Timeline()

    track = timeline.new_track(
        name="Subtitles",
        type=TrackType.SUBTITLE,
    )

    assert timeline.track_count == 1
    assert track.name == "Subtitles"
    assert track.type == TrackType.SUBTITLE
    assert timeline.subtitle_tracks == [track]


def test_timeline_empty_state() -> None:
    """A new timeline should be empty."""

    timeline = Timeline()

    assert timeline.is_empty is True
    assert timeline.track_count == 0
    assert timeline.clip_count == 0
    assert timeline.duration == pytest.approx(0.0)


def test_timeline_clear(timeline: Timeline) -> None:
    """clear should remove timeline editing objects."""

    assert timeline.track_count == 2
    assert timeline.clip_count == 2

    timeline.clear()

    assert timeline.track_count == 0
    assert timeline.clip_count == 0
    assert timeline.is_empty is True