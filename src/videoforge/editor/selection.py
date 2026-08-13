"""
VideoForge Selection Manager

Centralized management of editor selections.

The SelectionManager tracks the user's current selection across
the editor. Other editing systems (move, delete, clipboard,
trim, ripple, grouping, etc.) should operate on the current
selection instead of directly manipulating Timeline objects.
"""

from __future__ import annotations

from collections.abc import Iterable

from videoforge.media.clip import Clip
from videoforge.media.effect import Effect
from videoforge.media.marker import Marker
from videoforge.media.overlay import Overlay
from videoforge.media.track import Track


class SelectionManager:
    """
    Stores the current editor selection.

    Supports multiple selected objects simultaneously.
    """

    def __init__(self) -> None:
        self._clips: list[Clip] = []
        self._tracks: list[Track] = []
        self._overlays: list[Overlay] = []
        self._markers: list[Marker] = []
        self._effects: list[Effect] = []

    # ==========================================================
    # Clear
    # ==========================================================

    def clear(self) -> None:
        """Clear every selection."""

        self.clear_clips()
        self.clear_tracks()
        self.clear_overlays()
        self.clear_markers()
        self.clear_effects()

    # ==========================================================
    # Clip Selection
    # ==========================================================

    @property
    def clips(self) -> list[Clip]:
        return self._clips

    @property
    def selected_clips(self) -> list[Clip]:
        return self._clips

    def select_clip(
        self,
        clip: Clip,
        additive: bool = True,
    ) -> None:

        if not additive:
            self.clear_clips()

        if clip not in self._clips:
            self._clips.append(clip)
            clip.selected = True

    def select_clips(
        self,
        clips: Iterable[Clip],
        additive: bool = False,
    ) -> None:

        if not additive:
            self.clear_clips()

        for clip in clips:
            self.select_clip(
                clip,
                additive=True,
            )

    def deselect_clip(
        self,
        clip: Clip,
    ) -> None:

        if clip in self._clips:
            self._clips.remove(clip)
            clip.selected = False

    def toggle_clip(
        self,
        clip: Clip,
    ) -> None:

        if clip in self._clips:
            self.deselect_clip(clip)
        else:
            self.select_clip(clip)

    def clear_clips(self) -> None:

        for clip in self._clips:
            clip.selected = False

        self._clips.clear()

    def is_clip_selected(
        self,
        clip: Clip,
    ) -> bool:

        return clip in self._clips

    # ==========================================================
    # Track Selection
    # ==========================================================

    @property
    def tracks(self) -> list[Track]:
        return self._tracks

    def select_track(
        self,
        track: Track,
        additive: bool = True,
    ) -> None:

        if not additive:
            self.clear_tracks()

        if track not in self._tracks:
            self._tracks.append(track)

    def deselect_track(
        self,
        track: Track,
    ) -> None:

        if track in self._tracks:
            self._tracks.remove(track)

    def clear_tracks(self) -> None:
        self._tracks.clear()

    # ==========================================================
    # Overlay Selection
    # ==========================================================

    @property
    def overlays(self) -> list[Overlay]:
        return self._overlays

    def select_overlay(
        self,
        overlay: Overlay,
        additive: bool = True,
    ) -> None:

        if not additive:
            self.clear_overlays()

        if overlay not in self._overlays:
            self._overlays.append(overlay)

    def deselect_overlay(
        self,
        overlay: Overlay,
    ) -> None:

        if overlay in self._overlays:
            self._overlays.remove(overlay)

    def clear_overlays(self) -> None:
        self._overlays.clear()

    # ==========================================================
    # Marker Selection
    # ==========================================================

    @property
    def markers(self) -> list[Marker]:
        return self._markers

    def select_marker(
        self,
        marker: Marker,
        additive: bool = True,
    ) -> None:

        if not additive:
            self.clear_markers()

        if marker not in self._markers:
            self._markers.append(marker)

    def deselect_marker(
        self,
        marker: Marker,
    ) -> None:

        if marker in self._markers:
            self._markers.remove(marker)

    def clear_markers(self) -> None:
        self._markers.clear()

    # ==========================================================
    # Effect Selection
    # ==========================================================

    @property
    def effects(self) -> list[Effect]:
        return self._effects

    def select_effect(
        self,
        effect: Effect,
        additive: bool = True,
    ) -> None:

        if not additive:
            self.clear_effects()

        if effect not in self._effects:
            self._effects.append(effect)

    def deselect_effect(
        self,
        effect: Effect,
    ) -> None:

        if effect in self._effects:
            self._effects.remove(effect)

    def clear_effects(self) -> None:
        self._effects.clear()

    # ==========================================================
    # Queries
    # ==========================================================

    @property
    def has_selection(self) -> bool:
        return (
            bool(self._clips)
            or bool(self._tracks)
            or bool(self._overlays)
            or bool(self._markers)
            or bool(self._effects)
        )

    @property
    def clip_count(self) -> int:
        return len(self._clips)

    @property
    def track_count(self) -> int:
        return len(self._tracks)

    @property
    def overlay_count(self) -> int:
        return len(self._overlays)

    @property
    def marker_count(self) -> int:
        return len(self._markers)

    @property
    def effect_count(self) -> int:
        return len(self._effects)

    # ==========================================================
    # Representation
    # ==========================================================

    def __len__(self) -> int:
        return (
            self.clip_count
            + self.track_count
            + self.overlay_count
            + self.marker_count
            + self.effect_count
        )

    def __bool__(self) -> bool:
        return self.has_selection

    def __repr__(self) -> str:
        return (
            "SelectionManager("
            f"clips={self.clip_count}, "
            f"tracks={self.track_count}, "
            f"overlays={self.overlay_count}, "
            f"markers={self.marker_count}, "
            f"effects={self.effect_count})"
        )
