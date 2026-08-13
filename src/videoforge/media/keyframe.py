"""
VideoForge Project

A project is the top-level container for one or more timelines along with
project metadata and settings.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from uuid import uuid4

from pydantic import BaseModel, Field, computed_field

from videoforge.media.timeline import Timeline


class Project(BaseModel):
    """
    Represents an editable VideoForge project.

    A project may contain multiple timelines (sequences), although one
    timeline is typically marked as the active timeline.
    """

    id: str = Field(default_factory=lambda: uuid4().hex)

    name: str = "Untitled Project"

    description: str | None = None

    timelines: list[Timeline] = Field(default_factory=list)

    active_timeline: int = 0

    metadata: dict[str, str] = Field(default_factory=dict)

    created_at: datetime = Field(default_factory=datetime.now)

    updated_at: datetime = Field(default_factory=datetime.now)

    version: str = "1.0"

    # ------------------------------------------------------------------

    def touch(self) -> None:
        """
        Update the modification timestamp.
        """
        self.updated_at = datetime.now()

    # ------------------------------------------------------------------

    def add_timeline(
        self,
        timeline: Timeline,
    ) -> Timeline:
        """
        Add a timeline to the project.
        """
        self.timelines.append(timeline)
        self.touch()
        return timeline

    # ------------------------------------------------------------------

    def remove_timeline(
        self,
        index: int,
    ) -> Timeline:

        timeline = self.timelines.pop(index)

        if self.active_timeline >= len(self.timelines):
            self.active_timeline = max(
                0,
                len(self.timelines) - 1,
            )

        self.touch()

        return timeline

    # ------------------------------------------------------------------

    def get_timeline(
        self,
        index: int,
    ) -> Timeline:

        return self.timelines[index]

    # ------------------------------------------------------------------

    @property
    def current_timeline(self) -> Timeline | None:
        """
        Returns the active timeline.
        """
        if not self.timelines:
            return None

        return self.timelines[self.active_timeline]

    # ------------------------------------------------------------------

    def set_active_timeline(
        self,
        index: int,
    ) -> None:

        if not 0 <= index < len(self.timelines):
            raise IndexError("Timeline index out of range.")

        self.active_timeline = index
        self.touch()

    # ------------------------------------------------------------------

    def rename(
        self,
        name: str,
    ) -> None:

        self.name = name
        self.touch()

    # ------------------------------------------------------------------

    @computed_field
    @property
    def timeline_count(self) -> int:
        return len(self.timelines)

    # ------------------------------------------------------------------

    @computed_field
    @property
    def total_tracks(self) -> int:

        return sum(len(timeline.tracks) for timeline in self.timelines)

    # ------------------------------------------------------------------

    @computed_field
    @property
    def total_clips(self) -> int:

        return sum(timeline.clip_count for timeline in self.timelines)

    # ------------------------------------------------------------------

    @computed_field
    @property
    def duration(self) -> float:

        if not self.timelines:
            return 0.0

        return max(timeline.duration for timeline in self.timelines)

    # ------------------------------------------------------------------

    @computed_field
    @property
    def is_empty(self) -> bool:
        return self.total_clips == 0

    # ------------------------------------------------------------------

    def save(
        self,
        path: str | Path,
    ) -> Path:
        """
        Save the project as JSON.
        """
        path = Path(path)

        path.write_text(
            self.model_dump_json(indent=2),
            encoding="utf-8",
        )

        return path

    # ------------------------------------------------------------------

    @classmethod
    def load(
        cls,
        path: str | Path,
    ) -> Project:
        """
        Load a project from disk.
        """
        path = Path(path)

        return cls.model_validate_json(path.read_text(encoding="utf-8"))

    # ------------------------------------------------------------------

    def __repr__(self) -> str:

        return (
            f"Project("
            f"name={self.name!r}, "
            f"timelines={self.timeline_count}, "
            f"clips={self.total_clips}, "
            f"duration={self.duration:.2f}s"
            f")"
        )
