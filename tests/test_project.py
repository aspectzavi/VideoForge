"""
Fast, pytest-based tests for Project (media/project.py).
"""

from __future__ import annotations

from pathlib import Path

import pytest

from videoforge.media.project import Project
from videoforge.media.timeline import Timeline


def test_defaults() -> None:
    project = Project()

    assert project.name == "Untitled Project"
    assert project.timeline_count == 1  # starts with one timeline
    assert project.composition_count == 0
    assert project.active_composition is None
    assert project.is_empty is True


def test_timeline_property_returns_active_timeline() -> None:
    project = Project()
    assert project.timeline is project.timelines[0]


def test_composition_property_none_when_no_active() -> None:
    project = Project()
    assert project.composition is None


def test_add_and_new_timeline() -> None:
    project = Project()

    tl = project.new_timeline()

    assert project.timeline_count == 2
    assert tl in project.timelines


def test_remove_timeline_adjusts_active_index() -> None:
    project = Project()
    second = project.new_timeline()

    project.active_timeline = 1
    project.remove_timeline(second)

    assert project.timeline_count == 1
    assert project.active_timeline == 0


def test_add_and_new_composition() -> None:
    project = Project()

    comp = project.new_composition("Intro")

    assert project.composition_count == 1
    assert project.active_composition == 0
    assert project.composition is comp


def test_remove_composition_resets_active_index() -> None:
    project = Project()
    comp = project.new_composition("Intro")

    project.remove_composition(comp)

    assert project.composition_count == 0
    assert project.active_composition is None


def test_asset_count_delegates_to_library() -> None:
    project = Project()
    project.media_library.import_file(Path("tests/sample_media/input.mp4"))

    assert project.asset_count == 1
    assert project.is_empty is False


def test_duration_delegates_to_active_timeline() -> None:
    project = Project()
    assert project.duration == project.timeline.duration


def test_clear_resets_everything() -> None:
    project = Project()
    project.media_library.import_file(Path("tests/sample_media/input.mp4"))
    project.new_composition("Intro")
    project.new_timeline()
    project.metadata["key"] = "value"

    project.clear()

    assert project.is_empty is True
    assert project.timeline_count == 1
    assert project.composition_count == 0
    assert project.active_composition is None
    assert project.metadata == {}


def test_clone_gets_new_id_and_is_independent() -> None:
    project = Project(name="Original")

    clone = project.clone()

    assert clone.id != project.id
    assert clone.name == "Original"

    clone.name = "Changed"
    assert project.name == "Original"


def test_summary() -> None:
    project = Project(name="My Project")

    summary = project.summary()

    assert summary["name"] == "My Project"
    assert summary["timelines"] == 1


def test_save_and_load_roundtrip(tmp_path: Path) -> None:
    project = Project(name="Roundtrip Project")
    path = tmp_path / "project.json"

    # Project (media/project.py) doesn't define save()/load() itself -
    # only the other, unreferenced Project-shaped class formerly in
    # keyframe.py did. Documenting that here since it's easy to assume
    # otherwise given the class name collision.
    assert not hasattr(project, "save")
    assert not hasattr(Project, "load")

    path.write_text(project.model_dump_json(), encoding="utf-8")
    loaded = Project.model_validate_json(path.read_text(encoding="utf-8"))

    assert loaded.name == "Roundtrip Project"


def test_str_and_repr() -> None:
    project = Project(name="My Project")
    assert str(project) == "My Project"
    assert "Project" in repr(project)
