"""
VideoForge Clipboard

Clipboard support for VideoForge.

The clipboard stores deep copies of timeline objects so they can be
copied, cut, duplicated and pasted anywhere in the editor.

Initially the clipboard focuses on Clips, but it is designed so support
for transitions, overlays, compositions and effects can be added later.
"""

from __future__ import annotations

from videoforge.media.clip import Clip
from videoforge.media.timeline import Timeline
from videoforge.media.track import Track


class Clipboard:
    """
    Editor clipboard.

    Stores copies rather than references.
    """

    def __init__(self) -> None:

        self.clear()

    # ==========================================================
    # State
    # ==========================================================

    def clear(self) -> None:
        self._clips: list[Clip] = []
        self._relative_positions: list[float] = []

    @property
    def clips(self) -> list[Clip]:
        return self._clips

    @property
    def clip_count(self) -> int:
        return len(self._clips)

    @property
    def empty(self) -> bool:
        return len(self._clips) == 0

    # ==========================================================
    # Copy
    # ==========================================================

    def copy_clip(
        self,
        clip: Clip,
    ) -> None:
        """
        Copy one clip.
        """

        self.clear()

        clone = clip.clone()

        self._clips.append(clone)
        self._relative_positions.append(0.0)

    def copy_clips(
        self,
        clips: list[Clip],
    ) -> None:
        """
        Copy multiple clips while preserving
        their relative timing.
        """

        self.clear()

        if not clips:
            return

        ordered = sorted(
            clips,
            key=lambda c: c.timeline_start,
        )

        base = ordered[0].timeline_start

        for clip in ordered:
            self._clips.append(clip.clone())

            self._relative_positions.append(clip.timeline_start - base)

    # ==========================================================
    # Cut
    # ==========================================================

    def cut_clip(
        self,
        track: Track,
        clip: Clip,
    ) -> None:

        self.copy_clip(clip)
        track.remove_clip(clip)

    def cut_clips(
        self,
        track: Track,
        clips: list[Clip],
    ) -> None:

        self.copy_clips(clips)

        for clip in list(clips):
            if clip in track.clips:
                track.remove_clip(clip)

    # ==========================================================
    # Duplicate
    # ==========================================================

    def duplicate_clip(
        self,
        track: Track,
        clip: Clip,
        offset: float = 1.0,
    ) -> Clip:

        clone = clip.clone()

        clone.move(clip.timeline_end + offset)

        track.add_clip(clone)

        return clone

    def duplicate_clips(
        self,
        track: Track,
        clips: list[Clip],
        offset: float = 1.0,
    ) -> list[Clip]:

        new_clips: list[Clip] = []

        for clip in clips:
            new_clips.append(
                self.duplicate_clip(
                    track,
                    clip,
                    offset,
                )
            )

        return new_clips

    # ==========================================================
    # Paste
    # ==========================================================

    def paste(
        self,
        track: Track,
        timeline_position: float,
    ) -> list[Clip]:
        """
        Paste clipboard contents into a track.
        """

        pasted: list[Clip] = []

        for clip, relative in zip(
            self._clips,
            self._relative_positions,
            strict=False,
        ):
            clone = clip.clone()

            clone.move(timeline_position + relative)

            track.add_clip(clone)

            pasted.append(clone)

        return pasted

    # ==========================================================
    # Timeline Helpers
    # ==========================================================

    def copy_selected(
        self,
        timeline: Timeline,
    ) -> None:
        """
        Copy every selected clip in the timeline.
        """

        selected: list[Clip] = []

        for track in timeline.tracks:
            for clip in track.clips:
                if clip.selected:
                    selected.append(clip)

        self.copy_clips(selected)

    def cut_selected(
        self,
        timeline: Timeline,
    ) -> None:
        """
        Cut every selected clip.
        """

        selected_by_track: dict[Track, list[Clip]] = {}

        for track in timeline.tracks:
            clips = [clip for clip in track.clips if clip.selected]

            if clips:
                selected_by_track[track] = clips

        all_selected: list[Clip] = []

        for clips in selected_by_track.values():
            all_selected.extend(clips)

        self.copy_clips(all_selected)

        for track, clips in selected_by_track.items():
            for clip in clips:
                track.remove_clip(clip)

    # ==========================================================
    # Queries
    # ==========================================================

    def has_data(self) -> bool:
        return not self.empty

    # ==========================================================
    # Representation
    # ==========================================================

    def __len__(self) -> int:
        return self.clip_count

    def __bool__(self) -> bool:
        return self.has_data()

    def __repr__(self) -> str:

        return f"Clipboard(clips={self.clip_count})"
