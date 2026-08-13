"""
VideoForge Project

A Project is the root object of VideoForge.

It owns:

- Media Library
- Timelines
- Compositions
- Project metadata
- Render settings
- User settings

Everything saved to disk originates here.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, computed_field

from videoforge.media.composition import Composition
from videoforge.media.library import MediaLibrary
from videoforge.media.timeline import Timeline


class Project(BaseModel):
    """
    Root VideoForge project.
    """

    model_config = ConfigDict(
        arbitrary_types_allowed=True,
    )

    # ==========================================================
    # Identity
    # ==========================================================

    id: str = Field(
        default_factory=lambda: uuid.uuid4().hex,
    )

    name: str = "Untitled Project"

    description: str = ""

    path: Path | None = None

    # ==========================================================
    # Dates
    # ==========================================================

    created_at: datetime = Field(
        default_factory=datetime.utcnow,
    )

    modified_at: datetime = Field(
        default_factory=datetime.utcnow,
    )

    # ==========================================================
    # Media
    # ==========================================================

    media_library: MediaLibrary = Field(
        default_factory=MediaLibrary,
    )

    # ==========================================================
    # Timelines
    # ==========================================================

    timelines: list[Timeline] = Field(
        default_factory=lambda: [Timeline()],
    )

    active_timeline: int = 0

    # ==========================================================
    # Compositions
    # ==========================================================

    compositions: list[Composition] = Field(
        default_factory=list,
    )

    active_composition: int | None = None

    # ==========================================================
    # Metadata
    # ==========================================================

    metadata: dict[str, Any] = Field(
        default_factory=dict,
    )

    # ==========================================================
    # Computed
    # ==========================================================

    @computed_field
    @property
    def timeline(self) -> Timeline:
        return self.timelines[self.active_timeline]

    @computed_field
    @property
    def composition(self) -> Composition | None:
        if self.active_composition is None:
            return None

        return self.compositions[self.active_composition]

    @computed_field
    @property
    def duration(self) -> float:
        return self.timeline.duration

    @computed_field
    @property
    def asset_count(self) -> int:
        return self.media_library.asset_count

    @computed_field
    @property
    def timeline_count(self) -> int:
        return len(self.timelines)

    @computed_field
    @property
    def composition_count(self) -> int:
        return len(self.compositions)

    @computed_field
    @property
    def is_empty(self) -> bool:
        return self.asset_count == 0 and self.timeline.clip_count == 0

    # ==========================================================
    # Timeline Management
    # ==========================================================

    def add_timeline(
        self,
        timeline: Timeline,
    ) -> Timeline:

        self.timelines.append(timeline)
        self.modified_at = datetime.utcnow()

        return timeline

    def new_timeline(
        self,
    ) -> Timeline:

        timeline = Timeline()

        self.add_timeline(timeline)

        return timeline

    def remove_timeline(
        self,
        timeline: Timeline,
    ) -> None:

        if timeline in self.timelines:
            self.timelines.remove(timeline)

            self.active_timeline = min(
                self.active_timeline,
                max(0, len(self.timelines) - 1),
            )

            self.modified_at = datetime.utcnow()

    # ==========================================================
    # Composition Management
    # ==========================================================

    def add_composition(
        self,
        composition: Composition,
    ) -> Composition:

        self.compositions.append(composition)

        if self.active_composition is None:
            self.active_composition = 0

        self.modified_at = datetime.utcnow()

        return composition

    def new_composition(
        self,
        name: str = "Composition",
    ) -> Composition:

        composition = Composition(name=name)

        self.add_composition(composition)

        return composition

    def remove_composition(
        self,
        composition: Composition,
    ) -> None:

        if composition in self.compositions:
            index = self.compositions.index(composition)

            self.compositions.remove(composition)

            if self.active_composition == index:
                self.active_composition = 0 if self.compositions else None

            self.modified_at = datetime.utcnow()

    # ==========================================================
    # Utilities
    # ==========================================================

    def touch(self) -> None:
        """
        Update modification timestamp.
        """
        self.modified_at = datetime.utcnow()

    def clear(self) -> None:
        """
        Reset project.
        """
        self.media_library.clear()

        self.timelines = [Timeline()]

        self.active_timeline = 0

        self.compositions.clear()

        self.active_composition = None

        self.metadata.clear()

        self.touch()

    def clone(self) -> Project:
        """
        Deep copy project.
        """
        clone = self.model_copy(
            deep=True,
        )

        clone.id = uuid.uuid4().hex

        return clone

    def summary(self) -> dict[str, Any]:

        return {
            "name": self.name,
            "assets": self.asset_count,
            "timelines": self.timeline_count,
            "compositions": self.composition_count,
            "duration": self.duration,
        }

    # ==========================================================
    # Representation
    # ==========================================================

    def __str__(self) -> str:
        return self.name

    def __repr__(self) -> str:

        return (
            "Project("
            f"name='{self.name}', "
            f"assets={self.asset_count}, "
            f"timelines={self.timeline_count}, "
            f"compositions={self.composition_count}, "
            f"duration={self.duration:.2f}s)"
        )
