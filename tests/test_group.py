"""
Fast, pytest-based tests for GroupManager (editor/group.py).
"""

from __future__ import annotations

from pathlib import Path

import pytest

from videoforge.editor.group import GroupManager
from videoforge.media.asset import MediaAsset
from videoforge.media.clip import Clip
from videoforge.media.timeline import Timeline
from videoforge.media.track import Track

SAMPLE_MEDIA = Path("tests/sample_media/input.mp4")


@pytest.fixture
def asset() -> MediaAsset:
    return MediaAsset.load(SAMPLE_MEDIA)


def _clip(asset: MediaAsset, position: float) -> Clip:
    c = Clip(asset=asset)
    c.trim(0, 10)
    c.move(position)
    return c


@pytest.fixture
def timeline(asset: MediaAsset) -> Timeline:
    track = Track(name="V1")
    track.add_clip(_clip(asset, 0))
    track.add_clip(_clip(asset, 20))
    tl = Timeline()
    tl.add_track(track)
    return tl


@pytest.fixture
def manager(timeline: Timeline) -> GroupManager:
    return GroupManager(timeline)


def test_create_group_adds_clips(manager: GroupManager, timeline: Timeline) -> None:
    clips = timeline.tracks[0].clips
    group = manager.create_group(clips, name="My Group")

    assert group.name == "My Group"
    assert group.size == 2
    assert group.contains(clips[0])
    assert group.contains(clips[1])
    assert len(manager) == 1


def test_group_for_finds_containing_group(
    manager: GroupManager, timeline: Timeline
) -> None:
    clips = timeline.tracks[0].clips
    group = manager.create_group(clips)

    assert manager.group_for(clips[0]) is group


def test_group_for_returns_none_when_ungrouped(
    manager: GroupManager, timeline: Timeline
) -> None:
    assert manager.group_for(timeline.tracks[0].clips[0]) is None


def test_clips_returns_the_actual_clip_objects(
    manager: GroupManager, timeline: Timeline
) -> None:
    clips = timeline.tracks[0].clips
    group = manager.create_group([clips[0]])

    result = manager.clips(group)

    assert result == [clips[0]]


def test_remove_clip_deletes_group_when_empty(
    manager: GroupManager, timeline: Timeline
) -> None:
    clip = timeline.tracks[0].clips[0]
    group = manager.create_group([clip])

    manager.remove_clip(group, clip)

    assert len(manager) == 0


def test_ungroup_removes_clip_from_its_group(
    manager: GroupManager, timeline: Timeline
) -> None:
    clips = timeline.tracks[0].clips
    group = manager.create_group(clips)

    manager.ungroup(clips[0])

    assert group.contains(clips[0]) is False
    assert group.contains(clips[1]) is True


def test_delete_group(manager: GroupManager, timeline: Timeline) -> None:
    group = manager.create_group(timeline.tracks[0].clips)

    manager.delete_group(group)

    assert len(manager) == 0


def test_lock_unlock(manager: GroupManager, timeline: Timeline) -> None:
    group = manager.create_group(timeline.tracks[0].clips)

    manager.lock(group)
    assert group.locked is True

    manager.unlock(group)
    assert group.locked is False


def test_iteration(manager: GroupManager, timeline: Timeline) -> None:
    group = manager.create_group(timeline.tracks[0].clips)

    assert list(manager) == [group]
