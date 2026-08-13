"""
VideoForge Group Engine

Provides clip grouping functionality.

Grouped clips behave as a single logical object during
selection, movement, duplication and deletion.
"""

from __future__ import annotations

import uuid

from pydantic import BaseModel, Field

from videoforge.media.clip import Clip
from videoforge.media.timeline import Timeline

# ==========================================================
# Group Model
# ==========================================================


class ClipGroup(BaseModel):
    """
    Represents a logical group of clips.
    """

    id: str = Field(
        default_factory=lambda: uuid.uuid4().hex,
    )

    name: str = "Group"

    clip_ids: set[str] = Field(
        default_factory=set,
    )

    locked: bool = False

    def add(self, clip: Clip) -> None:
        self.clip_ids.add(clip.id)

    def remove(self, clip: Clip) -> None:
        self.clip_ids.discard(clip.id)

    def contains(self, clip: Clip) -> bool:
        return clip.id in self.clip_ids

    @property
    def size(self) -> int:
        return len(self.clip_ids)


# ==========================================================
# Group Manager
# ==========================================================


class GroupManager:
    """
    Manages clip groups.
    """

    def __init__(
        self,
        timeline: Timeline,
    ):
        self.timeline = timeline

        self.groups: dict[str, ClipGroup] = {}

    # ---------------------------------------------------------
    # Create
    # ---------------------------------------------------------

    def create_group(
        self,
        clips: list[Clip],
        name: str = "Group",
    ) -> ClipGroup:

        group = ClipGroup(
            name=name,
        )

        for clip in clips:
            group.add(clip)

        self.groups[group.id] = group

        return group

    # ---------------------------------------------------------
    # Delete
    # ---------------------------------------------------------

    def delete_group(
        self,
        group: ClipGroup,
    ) -> None:

        self.groups.pop(
            group.id,
            None,
        )

    # ---------------------------------------------------------
    # Lookup
    # ---------------------------------------------------------

    def group_for(
        self,
        clip: Clip,
    ) -> ClipGroup | None:

        for group in self.groups.values():
            if group.contains(clip):
                return group

        return None

    # ---------------------------------------------------------
    # Membership
    # ---------------------------------------------------------

    def add_clip(
        self,
        group: ClipGroup,
        clip: Clip,
    ) -> None:

        group.add(clip)

    def remove_clip(
        self,
        group: ClipGroup,
        clip: Clip,
    ) -> None:

        group.remove(clip)

        if group.size == 0:
            self.delete_group(group)

    # ---------------------------------------------------------
    # Query
    # ---------------------------------------------------------

    def clips(
        self,
        group: ClipGroup,
    ) -> list[Clip]:

        clip_ids = group.clip_ids

        results: list[Clip] = []

        for track in self.timeline.tracks:
            for clip in track.clips:
                if clip.id in clip_ids:
                    results.append(clip)

        return results

    # ---------------------------------------------------------
    # Ungroup
    # ---------------------------------------------------------

    def ungroup(
        self,
        clip: Clip,
    ) -> None:

        group = self.group_for(clip)

        if group is None:
            return

        group.remove(clip)

        if group.size == 0:
            self.delete_group(group)

    # ---------------------------------------------------------
    # Locking
    # ---------------------------------------------------------

    def lock(
        self,
        group: ClipGroup,
    ) -> None:

        group.locked = True

    def unlock(
        self,
        group: ClipGroup,
    ) -> None:

        group.locked = False

    # ---------------------------------------------------------
    # Iteration
    # ---------------------------------------------------------

    def __iter__(self):
        yield from self.groups.values()

    def __len__(self):
        return len(self.groups)
