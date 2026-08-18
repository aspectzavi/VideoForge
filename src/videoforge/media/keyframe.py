"""
VideoForge Keyframe

Represents animatable values that change over time.

Keyframes let clip/effect parameters be interpolated across a
timeline range (e.g. animating an Effect's brightness, or a Clip's
volume/opacity/position) rather than staying fixed for the whole
duration.

NOTE: This file previously contained an entire duplicate `Project`
class (identical purpose to media/project.py, but a simpler,
incompatible implementation) - confirmed via a full-repo search to be
completely unreferenced anywhere. That was almost certainly a
copy/paste or scaffolding error, since media/project.py already owns
the real Project. Replaced with real Keyframe/KeyframeTrack content,
which is what this filename actually promises and which the media/
subsystem was missing.
"""

from __future__ import annotations

import uuid
from enum import StrEnum

from pydantic import BaseModel, Field, computed_field


class InterpolationType(StrEnum):
    LINEAR = "linear"
    HOLD = "hold"  # step function - value snaps to the next keyframe
    EASE_IN = "ease_in"
    EASE_OUT = "ease_out"
    EASE_IN_OUT = "ease_in_out"


def _ease(t: float, kind: InterpolationType) -> float:
    """
    Apply an easing curve to a normalized progress value t in [0, 1].
    """

    if kind == InterpolationType.EASE_IN:
        return t * t

    if kind == InterpolationType.EASE_OUT:
        return 1 - (1 - t) * (1 - t)

    if kind == InterpolationType.EASE_IN_OUT:
        return t * t * (3 - 2 * t)  # smoothstep

    return t  # linear (HOLD is handled by the caller before this runs)


class Keyframe(BaseModel):
    """
    A single keyframe: a value at a specific time.

    `interpolation` describes how values are blended FROM the
    previous keyframe TO this one (matching common NLE conventions -
    the curve belongs to the segment ending at this keyframe).
    """

    id: str = Field(default_factory=lambda: uuid.uuid4().hex)
    time: float = Field(ge=0.0)
    value: float
    interpolation: InterpolationType = InterpolationType.LINEAR

    def __repr__(self) -> str:
        return (
            f"Keyframe(time={self.time}, value={self.value}, "
            f"interpolation={self.interpolation.value})"
        )


class KeyframeTrack(BaseModel):
    """
    Animates a single named parameter (e.g. "opacity", "volume",
    "scale") over time via a sorted set of Keyframes.
    """

    name: str
    keyframes: list[Keyframe] = Field(default_factory=list)

    # ------------------------------------------------------------------
    # Computed
    # ------------------------------------------------------------------

    @computed_field
    @property
    def is_empty(self) -> bool:
        return len(self.keyframes) == 0

    @computed_field
    @property
    def keyframe_count(self) -> int:
        return len(self.keyframes)

    @computed_field
    @property
    def start_time(self) -> float | None:
        if not self.keyframes:
            return None
        return min(kf.time for kf in self.keyframes)

    @computed_field
    @property
    def end_time(self) -> float | None:
        if not self.keyframes:
            return None
        return max(kf.time for kf in self.keyframes)


    # ------------------------------------------------------------------
    # Keyframe management
    # ------------------------------------------------------------------

    def add_keyframe(
        self,
        time: float,
        value: float,
        interpolation: InterpolationType = InterpolationType.LINEAR,
    ) -> Keyframe:
        """
        Add a keyframe, replacing any existing keyframe at the same
        time.
        """

        existing = self.keyframe_at(time)

        if existing is not None:
            self.keyframes.remove(existing)

        kf = Keyframe(time=time, value=value, interpolation=interpolation)
        self.keyframes.append(kf)
        self._sort()

        return kf

    def remove_keyframe(self, keyframe: Keyframe) -> bool:
        if keyframe not in self.keyframes:
            return False

        self.keyframes.remove(keyframe)
        return True

    def keyframe_at(self, time: float, tolerance: float = 1e-6) -> Keyframe | None:
        for kf in self.keyframes:
            if abs(kf.time - time) <= tolerance:
                return kf
        return None

    def clear(self) -> None:
        self.keyframes.clear()

    def _sort(self) -> None:
        self.keyframes.sort(key=lambda kf: kf.time)

    # ------------------------------------------------------------------
    # Evaluation
    # ------------------------------------------------------------------

    def value_at(self, time: float) -> float | None:
        """
        Interpolate the animated value at a given time.

        Returns None if there are no keyframes. Clamps to the first/
        last keyframe's value outside the keyframed range.
        """

        if not self.keyframes:
            return None

        self._sort()

        if time <= self.keyframes[0].time:
            return self.keyframes[0].value

        if time >= self.keyframes[-1].time:
            return self.keyframes[-1].value

        for i in range(len(self.keyframes) - 1):
            left = self.keyframes[i]
            right = self.keyframes[i + 1]

            if left.time <= time <= right.time:
                if right.interpolation == InterpolationType.HOLD:
                    return left.value

                span = right.time - left.time

                if span <= 0:
                    return right.value

                t = (time - left.time) / span
                eased_t = _ease(t, right.interpolation)

                return left.value + (right.value - left.value) * eased_t

        return self.keyframes[-1].value  # unreachable safety fallback

    # ------------------------------------------------------------------
    # Utilities
    # ------------------------------------------------------------------

    def clone(self) -> KeyframeTrack:
        clone = self.model_copy(deep=True)

        for kf in clone.keyframes:
            kf.id = uuid.uuid4().hex

        return clone

    def __len__(self) -> int:
        return len(self.keyframes)

    def __repr__(self) -> str:
        return f"KeyframeTrack(name={self.name!r}, keyframes={self.keyframe_count})"
