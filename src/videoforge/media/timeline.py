"""
VideoForge Timeline

Central editing model for VideoForge.

A Timeline represents an entire non-linear edit. It owns every editable
object in a project while the MediaLibrary owns the imported media.

Renderer, editor, exporter and playback engine should operate through
this class.
"""

from __future__ import annotations

from collections.abc import Iterator
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, computed_field

from videoforge.media.clip import Clip
from videoforge.media.effect import Effect
from videoforge.media.library import MediaLibrary
from videoforge.media.marker import Marker
from videoforge.media.overlay import Overlay
from videoforge.media.render_cache import RenderCache
from videoforge.media.selection import Selection
from videoforge.media.timeline_metadata import TimelineMetadata
from videoforge.media.timeline_settings import TimelineSettings
from videoforge.media.track import Track, TrackType
from videoforge.media.transition import Transition


class Timeline(BaseModel):
    """
    Complete editing timeline.
    """

    model_config = ConfigDict(
        arbitrary_types_allowed=True,
    )

    # ==========================================================
    # Core
    # ==========================================================

    metadata: TimelineMetadata = Field(
        default_factory=TimelineMetadata,
    )

    settings: TimelineSettings = Field(
        default_factory=TimelineSettings,
    )

    library: MediaLibrary = Field(
        default_factory=MediaLibrary,
    )

    # ==========================================================
    # Timeline Objects
    # ==========================================================

    tracks: list[Track] = Field(
        default_factory=list,
    )

    transitions: list[Transition] = Field(
        default_factory=list,
    )

    effects: list[Effect] = Field(
        default_factory=list,
    )

    overlays: list[Overlay] = Field(
        default_factory=list,
    )

    markers: list[Marker] = Field(
        default_factory=list,
    )

    selections: list[Selection] = Field(
        default_factory=list,
    )

    # ==========================================================
    # Cache
    # ==========================================================

    render_cache: RenderCache = Field(
        default_factory=RenderCache,
    )

    # ==========================================================
    # Custom metadata
    # ==========================================================

    metadata_dict: dict[str, Any] = Field(
        default_factory=dict,
    )

    # ==========================================================
    # Computed
    # ==========================================================

    @computed_field
    @property
    def duration(self) -> float:
        if not self.tracks:
            return 0.0

        return max(track.duration for track in self.tracks)

    @computed_field
    @property
    def track_count(self) -> int:
        return len(self.tracks)

    @computed_field
    @property
    def clip_count(self) -> int:
        return sum(track.clip_count for track in self.tracks)

    @computed_field
    @property
    def transition_count(self) -> int:
        return len(self.transitions)

    @computed_field
    @property
    def effect_count(self) -> int:
        return len(self.effects)

    @computed_field
    @property
    def overlay_count(self) -> int:
        return len(self.overlays)

    @computed_field
    @property
    def marker_count(self) -> int:
        return len(self.markers)

    @computed_field
    @property
    def asset_count(self) -> int:
        return self.library.asset_count

    @computed_field
    @property
    def video_tracks(self) -> list[Track]:
        return [t for t in self.tracks if t.type == TrackType.VIDEO]

    @computed_field
    @property
    def audio_tracks(self) -> list[Track]:
        return [t for t in self.tracks if t.type == TrackType.AUDIO]

    @computed_field
    @property
    def subtitle_tracks(self) -> list[Track]:
        return [t for t in self.tracks if t.type == TrackType.SUBTITLE]

    @computed_field
    @property
    def is_empty(self) -> bool:
        return self.clip_count == 0

    # ==========================================================
    # Track Management
    # ==========================================================

    def add_track(self, track: Track) -> Track:
        self.tracks.append(track)
        return track

    def new_track(
        self,
        name: str,
        type: TrackType = TrackType.VIDEO,
    ) -> Track:
        track = Track(
            name=name,
            type=type,
        )
        self.tracks.append(track)
        return track

    def remove_track(self, track: Track) -> None:
        if track in self.tracks:
            self.tracks.remove(track)

    def get_track(
        self,
        track_id: str,
    ) -> Track | None:
        return next(
            (t for t in self.tracks if t.id == track_id),
            None,
        )

    # ==========================================================
    # Clip Queries
    # ==========================================================

    def clips_at(
        self,
        time: float,
    ) -> list[Clip]:

        clips: list[Clip] = []

        for track in self.tracks:
            if not track.enabled:
                continue

            for clip in track.clips:
                if clip.enabled and clip.timeline_start <= time < clip.timeline_end:
                    clips.append(clip)

        return clips

    def clip_at(
        self,
        time: float,
    ) -> Clip | None:
        """
        Return the first enabled clip containing the given timeline time.

        Tracks are searched in timeline order. Disabled tracks and disabled
        clips are ignored.
        """

        for track in self.tracks:
            if not track.enabled:
                continue

            clip = track.clip_at(time)

            if clip is not None and clip.enabled:
                return clip

        return None

    def all_clips(self) -> list[Clip]:

        clips: list[Clip] = []

        for track in self.tracks:
            clips.extend(track.clips)

        clips.sort(
            key=lambda c: (
                c.timeline_start,
                c.track_index,
            )
        )

        return clips

    def enabled_clips(self) -> list[Clip]:

        return [clip for clip in self.all_clips() if clip.enabled]

    # ==========================================================
    # Timeline Editing
    # ==========================================================

    def ripple(
        self,
        start_time: float,
        delta: float,
    ) -> None:

        for track in self.tracks:
            track.ripple(start_time, delta)

    # ==========================================================
    # Iterators
    # ==========================================================

    def iter_tracks(self) -> Iterator[Track]:
        yield from self.tracks

    def iter_clips(self) -> Iterator[Clip]:
        yield from self.all_clips()

    def flatten(self) -> list[Clip]:
        return self.all_clips()

    # ==========================================================
    # Reset
    # ==========================================================

    def clear(self) -> None:

        self.tracks.clear()
        self.transitions.clear()
        self.effects.clear()
        self.overlays.clear()
        self.markers.clear()
        self.selections.clear()

        self.library.clear()
        self.render_cache.clear()

    # ==========================================================
    # Representation
    # ==========================================================

    def __str__(self) -> str:
        return self.metadata.name

    def __repr__(self) -> str:
        return (
            f"Timeline("
            f"name='{self.metadata.name}', "
            f"tracks={self.track_count}, "
            f"clips={self.clip_count}, "
            f"assets={self.asset_count}, "
            f"duration={self.duration:.2f}s)"
        )
