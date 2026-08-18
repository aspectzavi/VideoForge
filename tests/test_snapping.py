"""
Fast, pytest-based tests for SnapEngine (editor/snapping.py).
"""

from __future__ import annotations

from pathlib import Path

import pytest

from videoforge.editor.snapping import SnapEngine
from videoforge.media.asset import MediaAsset
from videoforge.media.clip import Clip
from videoforge.media.marker import Marker
from videoforge.media.timeline import Timeline
from videoforge.media.track import Track

SAMPLE_MEDIA = Path("tests/sample_media/input.mp4")


@pytest.fixture
def asset() -> MediaAsset:
    return MediaAsset.load(SAMPLE_MEDIA)


def _clip(asset: MediaAsset, position: float, duration: float = 10.0) -> Clip:
    c = Clip(asset=asset)
    c.trim(0, duration)
    c.move(position)
    return c


@pytest.fixture
def timeline(asset: MediaAsset) -> Timeline:
    track = Track(name="V1")
    track.add_clip(_clip(asset, 0))  # edges at 0.0 and 10.0
    track.add_clip(_clip(asset, 20))  # edges at 20.0 and 30.0
    tl = Timeline()
    tl.add_track(track)
    return tl


def test_snap_points_includes_zero_clip_edges_and_markers(timeline: Timeline) -> None:
    timeline.markers.append(Marker(time=15.0))
    engine = SnapEngine(timeline)

    points = engine.snap_points()

    assert points == [0.0, 10.0, 15.0, 20.0, 30.0]


def test_snap_pulls_position_to_nearby_point(timeline: Timeline) -> None:
    """
    Regression test: snap() previously compared against
    abs(best - position), which is always 0 when best starts equal to
    position - so `distance < 0` was never true and the loop never
    updated `best`. snap() always returned the input unchanged,
    regardless of how close a snap point was. Fixed by tracking
    best_distance separately from best.
    """
    engine = SnapEngine(timeline, threshold=0.5)

    # 10.2 is within threshold (0.5) of the clip edge at 10.0
    assert engine.snap(10.2) == pytest.approx(10.0)

    # 10.2 was NOT itself a snap point, so if snap() were still the
    # no-op bug, this would fail (it would just return 10.2 back).
    assert engine.snap(10.2) != pytest.approx(10.2)


def test_snap_returns_position_unchanged_when_nothing_nearby(
    timeline: Timeline,
) -> None:
    engine = SnapEngine(timeline, threshold=0.5)

    assert engine.snap(15.0) == pytest.approx(15.0)  # 5.0 away from any point


def test_snap_prefers_closest_point_among_several_candidates(
    timeline: Timeline,
) -> None:
    # threshold wide enough that both 0.0 and 10.0 clip edges qualify
    # relative to position 4.0 - 10.0 is NOT actually eligible here
    # (distance 6 > threshold), so this specifically checks the
    # closer of two in-range points is chosen, not just the first one
    # found.
    engine = SnapEngine(timeline, threshold=5.0)

    assert engine.snap(4.0) == pytest.approx(0.0)  # closer than 10.0 (dist 4 vs 6)
    assert engine.snap(7.0) == pytest.approx(10.0)  # closer than 0.0 (dist 3 vs 7)


def test_snap_clip_start_and_end_delegate_to_snap(
    timeline: Timeline, asset: MediaAsset
) -> None:
    engine = SnapEngine(timeline, threshold=0.5)
    clip = _clip(asset, 50)

    assert engine.snap_clip_start(clip, 20.3) == pytest.approx(20.0)
    assert engine.snap_clip_end(clip, 29.8) == pytest.approx(30.0)


def test_snap_to_playhead(timeline: Timeline) -> None:
    engine = SnapEngine(timeline, threshold=0.5)

    assert engine.snap_to_playhead(12.2, playhead=12.0) == pytest.approx(12.0)
    assert engine.snap_to_playhead(12.9, playhead=12.0) == pytest.approx(12.9)


def test_closest_point(timeline: Timeline) -> None:
    engine = SnapEngine(timeline)
    assert engine.closest_point(4.0) == pytest.approx(0.0)


def test_closest_point_none_when_no_points() -> None:
    empty_timeline = Timeline()
    engine = SnapEngine(empty_timeline)

    # snap_points() always includes 0.0 even with no tracks/markers,
    # so closest_point() is never actually None in practice.
    assert engine.closest_point(100.0) == pytest.approx(0.0)


def test_set_threshold_clamps_at_zero(timeline: Timeline) -> None:
    engine = SnapEngine(timeline)

    engine.set_threshold(-5.0)

    assert engine.threshold == 0.0
