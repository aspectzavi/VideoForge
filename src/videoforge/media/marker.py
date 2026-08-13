"""
VideoForge Timeline Marker

Markers are annotations placed on a timeline or clip to identify important
positions such as edit points, chapters, comments, or synchronization cues.
"""

from __future__ import annotations

from enum import StrEnum
from uuid import uuid4

from pydantic import BaseModel, Field, computed_field

# =====================================================================
# Marker Types
# =====================================================================


class MarkerType(StrEnum):
    """Supported marker categories."""

    STANDARD = "standard"
    CHAPTER = "chapter"
    COMMENT = "comment"
    SYNC = "sync"
    IN = "in"
    OUT = "out"


# =====================================================================
# Marker Colors
# =====================================================================


class MarkerColor(StrEnum):
    """Common NLE marker colors."""

    RED = "red"
    ORANGE = "orange"
    YELLOW = "yellow"
    GREEN = "green"
    CYAN = "cyan"
    BLUE = "blue"
    PURPLE = "purple"
    PINK = "pink"
    WHITE = "white"


# =====================================================================
# Marker
# =====================================================================


class Marker(BaseModel):
    """
    Represents a marker placed on a timeline or clip.
    """

    id: str = Field(default_factory=lambda: uuid4().hex)

    name: str = "Marker"

    comment: str | None = None

    time: float = 0.0

    duration: float = 0.0

    color: MarkerColor = MarkerColor.YELLOW

    type: MarkerType = MarkerType.STANDARD

    tags: list[str] = Field(default_factory=list)

    metadata: dict[str, str] = Field(default_factory=dict)

    enabled: bool = True

    # -----------------------------------------------------------------

    def move(
        self,
        time: float,
    ) -> None:
        """
        Move the marker.
        """
        self.time = max(0.0, time)

    # -----------------------------------------------------------------

    def shift(
        self,
        seconds: float,
    ) -> None:
        """
        Shift the marker by a relative amount.
        """
        self.time = max(0.0, self.time + seconds)

    # -----------------------------------------------------------------

    def rename(
        self,
        name: str,
    ) -> None:
        self.name = name

    # -----------------------------------------------------------------

    def add_tag(
        self,
        tag: str,
    ) -> None:
        if tag not in self.tags:
            self.tags.append(tag)

    # -----------------------------------------------------------------

    def remove_tag(
        self,
        tag: str,
    ) -> None:
        if tag in self.tags:
            self.tags.remove(tag)

    # -----------------------------------------------------------------

    @computed_field
    @property
    def end(self) -> float:
        """
        End time for range markers.
        """
        return self.time + self.duration

    # -----------------------------------------------------------------

    @computed_field
    @property
    def is_range(self) -> bool:
        """
        True if the marker spans a duration.
        """
        return self.duration > 0

    # -----------------------------------------------------------------

    @computed_field
    @property
    def is_point(self) -> bool:
        """
        True if the marker is a single point.
        """
        return self.duration <= 0

    # -----------------------------------------------------------------

    @computed_field
    @property
    def has_comment(self) -> bool:
        return bool(self.comment)

    # -----------------------------------------------------------------

    def contains(
        self,
        time: float,
    ) -> bool:
        """
        Returns True if the supplied timeline time falls inside
        this marker.
        """

        if self.is_point:
            return abs(self.time - time) < 1e-6

        return self.time <= time <= self.end

    # -----------------------------------------------------------------

    def overlaps(
        self,
        start: float,
        end: float,
    ) -> bool:
        """
        Returns True if this marker overlaps a time range.
        """

        if self.is_point:
            return start <= self.time <= end

        return not (self.end < start or self.time > end)

    # -----------------------------------------------------------------

    def copy_marker(self) -> Marker:
        """
        Create a duplicate marker with a new ID.
        """

        marker = self.model_copy(deep=True)
        marker.id = uuid4().hex
        return marker

    # -----------------------------------------------------------------

    def __repr__(self) -> str:

        return (
            "Marker("
            f"name={self.name!r}, "
            f"time={self.time:.2f}, "
            f"duration={self.duration:.2f}, "
            f"type={self.type.value}"
            ")"
        )
