"""
VideoForge Selection

Represents the current editor selection.

Selections may contain clips, tracks, markers, assets, or any combination
thereof. This model is UI-agnostic and can be used by desktop, web, or
mobile editors.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field, computed_field

from videoforge.media.asset import MediaAsset
from videoforge.media.clip import Clip
from videoforge.media.marker import Marker
from videoforge.media.track import Track


class Selection(BaseModel):
    """
    Represents the current editor selection.
    """

    clips: list[Clip] = Field(default_factory=list)

    tracks: list[Track] = Field(default_factory=list)

    markers: list[Marker] = Field(default_factory=list)

    assets: list[MediaAsset] = Field(default_factory=list)

    metadata: dict[str, Any] = Field(default_factory=dict)

    # ------------------------------------------------------------------
    # Clear
    # ------------------------------------------------------------------

    def clear(self) -> None:
        self.clips.clear()
        self.tracks.clear()
        self.markers.clear()
        self.assets.clear()

    # ------------------------------------------------------------------
    # Clip Selection
    # ------------------------------------------------------------------

    def select_clip(
        self,
        clip: Clip,
        append: bool = False,
    ) -> None:

        if not append:
            self.clips.clear()

        if clip not in self.clips:
            self.clips.append(clip)

    def deselect_clip(
        self,
        clip: Clip,
    ) -> None:

        if clip in self.clips:
            self.clips.remove(clip)

    # ------------------------------------------------------------------
    # Track Selection
    # ------------------------------------------------------------------

    def select_track(
        self,
        track: Track,
        append: bool = False,
    ) -> None:

        if not append:
            self.tracks.clear()

        if track not in self.tracks:
            self.tracks.append(track)

    def deselect_track(
        self,
        track: Track,
    ) -> None:

        if track in self.tracks:
            self.tracks.remove(track)

    # ------------------------------------------------------------------
    # Marker Selection
    # ------------------------------------------------------------------

    def select_marker(
        self,
        marker: Marker,
        append: bool = False,
    ) -> None:

        if not append:
            self.markers.clear()

        if marker not in self.markers:
            self.markers.append(marker)

    def deselect_marker(
        self,
        marker: Marker,
    ) -> None:

        if marker in self.markers:
            self.markers.remove(marker)

    # ------------------------------------------------------------------
    # Asset Selection
    # ------------------------------------------------------------------

    def select_asset(
        self,
        asset: MediaAsset,
        append: bool = False,
    ) -> None:

        if not append:
            self.assets.clear()

        if asset not in self.assets:
            self.assets.append(asset)

    def deselect_asset(
        self,
        asset: MediaAsset,
    ) -> None:

        if asset in self.assets:
            self.assets.remove(asset)

    # ------------------------------------------------------------------
    # Queries
    # ------------------------------------------------------------------

    @computed_field
    @property
    def clip_count(self) -> int:
        return len(self.clips)

    @computed_field
    @property
    def track_count(self) -> int:
        return len(self.tracks)

    @computed_field
    @property
    def marker_count(self) -> int:
        return len(self.markers)

    @computed_field
    @property
    def asset_count(self) -> int:
        return len(self.assets)

    @computed_field
    @property
    def total_count(self) -> int:
        return self.clip_count + self.track_count + self.marker_count + self.asset_count

    @computed_field
    @property
    def is_empty(self) -> bool:
        return self.total_count == 0

    @computed_field
    @property
    def has_clips(self) -> bool:
        return bool(self.clips)

    @computed_field
    @property
    def has_tracks(self) -> bool:
        return bool(self.tracks)

    @computed_field
    @property
    def has_markers(self) -> bool:
        return bool(self.markers)

    @computed_field
    @property
    def has_assets(self) -> bool:
        return bool(self.assets)

    # ------------------------------------------------------------------
    # Convenience
    # ------------------------------------------------------------------

    @property
    def first_clip(self) -> Clip | None:
        return self.clips[0] if self.clips else None

    @property
    def first_track(self) -> Track | None:
        return self.tracks[0] if self.tracks else None

    @property
    def first_marker(self) -> Marker | None:
        return self.markers[0] if self.markers else None

    @property
    def first_asset(self) -> MediaAsset | None:
        return self.assets[0] if self.assets else None

    # ------------------------------------------------------------------

    def __len__(self) -> int:
        return self.total_count

    # ------------------------------------------------------------------

    def __repr__(self) -> str:
        return (
            "Selection("
            f"clips={self.clip_count}, "
            f"tracks={self.track_count}, "
            f"markers={self.marker_count}, "
            f"assets={self.asset_count}"
            ")"
        )
