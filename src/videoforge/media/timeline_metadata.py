"""
Timeline metadata.

Contains descriptive information about a timeline independent of its
tracks, clips, and render settings.
"""

from __future__ import annotations

from datetime import datetime
from uuid import uuid4

from pydantic import BaseModel, Field

from videoforge.engine.version import VERSION


class TimelineMetadata(BaseModel):
    """
    Descriptive metadata for a timeline.
    """

    id: str = Field(
        default_factory=lambda: uuid4().hex,
    )

    name: str = "Untitled Timeline"

    description: str | None = None

    author: str | None = None

    created_at: datetime = Field(
        default_factory=datetime.utcnow,
    )

    modified_at: datetime = Field(
        default_factory=datetime.utcnow,
    )

    version: str = VERSION

    # ---------------------------------------------------------

    def touch(self) -> None:
        """
        Update the modification timestamp.
        """

        self.modified_at = datetime.utcnow()

    # ---------------------------------------------------------

    def rename(
        self,
        name: str,
    ) -> None:
        """
        Rename the timeline.
        """

        self.name = name

        self.touch()

    # ---------------------------------------------------------

    def update_description(
        self,
        description: str | None,
    ) -> None:
        """
        Update the timeline description.
        """

        self.description = description

        self.touch()

    # ---------------------------------------------------------

    def update_author(
        self,
        author: str | None,
    ) -> None:
        """
        Update the timeline author.
        """

        self.author = author

        self.touch()

    # ---------------------------------------------------------

    @property
    def has_description(self) -> bool:

        return bool(self.description)

    # ---------------------------------------------------------

    @property
    def has_author(self) -> bool:

        return bool(self.author)

    # ---------------------------------------------------------

    def __str__(self) -> str:

        return self.name
