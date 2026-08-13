"""
VideoForge Track

A Track contains an ordered collection of Clips.

Tracks are the building blocks of a Timeline.
A timeline may contain multiple video and audio tracks.

Responsibilities
----------------
- Maintain clip ordering
- Detect overlaps
- Ripple editing
- Insert/remove clips
- Query clips
"""

from __future__ import annotations

import uuid
from collections.abc import Iterator
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, computed_field

from videoforge.media.clip import Clip
from videoforge.media.effect import Effect

# ==========================================================
# Track Type
# ==========================================================


class TrackType(StrEnum):
    VIDEO = "video"
    AUDIO = "audio"
    SUBTITLE = "subtitle"
    METADATA = "metadata"
    ADJUSTMENT = "adjustment"


# ==========================================================
# Track
# ==========================================================


class Track(BaseModel):
    model_config = ConfigDict(
        arbitrary_types_allowed=True,
    )

    # ---------------------------------------------------------

    id: str = Field(
        default_factory=lambda: uuid.uuid4().hex,
    )

    name: str = "Track"

    color: str = "#4A90E2"

    visible: bool = True

    collapsed: bool = False

    height: int = 72

    type: TrackType = TrackType.VIDEO

    enabled: bool = True

    locked: bool = False

    muted: bool = False

    solo: bool = False

    opacity: float = 1.0

    blend_mode: str = "normal"

    volume: float = 1.0

    pan: float = 0.0

    group: str | None = None

    parent_track: str | None = None

    clips: list[Clip] = Field(
        default_factory=list,
    )

    metadata: dict = Field(
        default_factory=dict,
    )

    effects: list[Effect] = Field(
        default_factory=list,
    )

    # ==========================================================
    # Computed
    # ==========================================================

    @computed_field
    @property
    def duration(self) -> float:

        if not self.clips:
            return 0.0

        return max(clip.timeline_end for clip in self.clips)

    @computed_field
    @property
    def clip_count(self) -> int:

        return len(self.clips)

    @computed_field
    @property
    def is_empty(self) -> bool:

        return len(self.clips) == 0

    @computed_field
    @property
    def enabled_clips(self) -> list[Clip]:
        return [clip for clip in self.clips if clip.enabled]

    @computed_field
    @property
    def locked_clips(self) -> int:
        return sum(clip.locked for clip in self.clips)

    @computed_field
    @property
    def selected_clips(self) -> list[Clip]:
        return [clip for clip in self.clips if clip.selected]

    @computed_field
    @property
    def start(self) -> float:

        if not self.clips:
            return 0.0

        return self.clips[0].timeline_start

    @computed_field
    @property
    def end(self) -> float:

        return self.duration

    # clip_sorting_helpers

    def sort(self) -> None:
        self._sort()

    def reverse(self) -> None:
        self.clips.reverse()

    # ==========================================================
    # Internal
    # ==========================================================

    def _sort(self) -> None:

        self.clips.sort(key=lambda c: c.timeline_start)

    # ==========================================================
    # Add / Remove
    # ==========================================================

    def add_clip(
        self,
        clip: Clip,
    ) -> Clip:

        self.clips.append(clip)

        self._sort()

        return clip

    def insert_clip(
        self,
        clip: Clip,
        position: float,
    ) -> Clip:

        clip.move(position)

        return self.add_clip(clip)

    def remove_clip(
        self,
        clip: Clip,
    ) -> None:

        self.clips.remove(clip)

    def remove_clip_by_id(
        self,
        clip_id: str,
    ) -> bool:

        for clip in self.clips:
            if clip.id == clip_id:
                self.clips.remove(clip)

                return True

        return False

    def clear(self) -> None:

        self.clips.clear()

    def set_color(
        self,
        color: str,
    ):
        self.color = color

    # ==========================================================
    # Lookup
    # ==========================================================

    def get_clip(
        self,
        clip_id: str,
    ) -> Clip | None:

        for clip in self.clips:
            if clip.id == clip_id:
                return clip

        return None

    def clip_at(
        self,
        seconds: float,
    ) -> Clip | None:

        for clip in self.clips:
            if clip.timeline_start <= seconds < clip.timeline_end:
                return clip

        return None

    # ==========================================================
    # Queries
    # ==========================================================

    def overlaps(
        self,
        clip: Clip,
    ) -> list[Clip]:

        overlaps: list[Clip] = []

        for other in self.clips:
            if other.id == clip.id:
                continue

            if (
                clip.timeline_start < other.timeline_end
                and clip.timeline_end > other.timeline_start
            ):
                overlaps.append(other)

        return overlaps

    def has_overlap(
        self,
        clip: Clip,
    ) -> bool:

        return bool(self.overlaps(clip))

    # ==========================================================
    # Ripple Editing
    # ==========================================================

    def ripple(
        self,
        start_time: float,
        delta: float,
    ) -> None:

        for clip in self.clips:
            if clip.timeline_start >= start_time:
                clip.offset(delta)

        self._sort()

    # ==========================================================
    # Movement
    # ==========================================================

    def move_clip(
        self,
        clip: Clip,
        new_position: float,
    ) -> None:

        clip.move(new_position)

        self._sort()

    # ==========================================================
    # Helpers
    # ==========================================================

    def first(self) -> Clip | None:

        if not self.clips:
            return None

        return self.clips[0]

    def last(self) -> Clip | None:

        if not self.clips:
            return None

        return self.clips[-1]

    def add_effect(
        self,
        effect: Effect,
    ):
        self.effects.append(effect)

    def remove_effect(
        self,
        effect: Effect,
    ):
        if effect in self.effects:
            self.effects.remove(effect)

    def clear_effects(self):
        self.effects.clear()

    # ==========================================================
    # Iteration
    # ==========================================================

    def iter_clips(self) -> Iterator[Clip]:
        """
        Iterate over clips in timeline order.
        """
        yield from self.clips

    def __len__(self):

        return len(self.clips)

    def __getitem__(
        self,
        index: int,
    ) -> Clip:

        return self.clips[index]

    # ==========================================================
    # Clone
    # ==========================================================

    def clone(self) -> Track:

        track = self.model_copy(
            deep=True,
        )

        track.id = uuid.uuid4().hex

        return track

    # ==========================================================
    # Representation
    # ==========================================================

    def __str__(self) -> str:

        return self.name

    def __repr__(self) -> str:

        return (
            f"Track("
            f"name='{self.name}', "
            f"type='{self.type.value}', "
            f"clips={len(self.clips)}, "
            f"duration={self.duration:.2f}s"
            f")"
        )

    # Track_Controls

    def mute(self):
        self.muted = True

    def unmute(self):
        self.muted = False

    def lock(self):
        self.locked = True

    def unlock(self):
        self.locked = False

    def enable(self):
        self.enabled = True

    def disable(self):
        self.enabled = False

    def show(self):
        self.visible = True

    def hide(self):
        self.visible = False
