"""
VideoForge Transition

Defines transitions that can be applied between two clips.

Transitions are editor-level objects. During rendering they are translated
into FFmpeg filter graphs (xfade, acrossfade, etc.).
"""

from __future__ import annotations

from enum import StrEnum
from uuid import uuid4

from pydantic import BaseModel, Field, computed_field

# =====================================================================
# Transition Types
# =====================================================================


class TransitionType(StrEnum):
    """
    Supported transition types.
    """

    CUT = "cut"

    FADE = "fade"

    DISSOLVE = "dissolve"

    CROSSFADE = "crossfade"

    WIPE_LEFT = "wipe_left"

    WIPE_RIGHT = "wipe_right"

    WIPE_UP = "wipe_up"

    WIPE_DOWN = "wipe_down"

    SLIDE_LEFT = "slide_left"

    SLIDE_RIGHT = "slide_right"

    SLIDE_UP = "slide_up"

    SLIDE_DOWN = "slide_down"

    ZOOM_IN = "zoom_in"

    ZOOM_OUT = "zoom_out"

    CIRCLE_OPEN = "circle_open"

    CIRCLE_CLOSE = "circle_close"

    RADIAL = "radial"

    PIXELIZE = "pixelize"

    BLUR = "blur"

    CUSTOM = "custom"


# =====================================================================
# Easing
# =====================================================================


class TransitionEasing(StrEnum):
    """
    Playback interpolation.
    """

    LINEAR = "linear"

    EASE_IN = "ease_in"

    EASE_OUT = "ease_out"

    EASE_IN_OUT = "ease_in_out"


# =====================================================================
# Transition
# =====================================================================


class Transition(BaseModel):
    """
    Represents a transition between two clips.
    """

    id: str = Field(default_factory=lambda: uuid4().hex)

    name: str | None = None

    type: TransitionType = TransitionType.CROSSFADE

    duration: float = 1.0

    offset: float = 0.0

    easing: TransitionEasing = TransitionEasing.LINEAR

    enabled: bool = True

    metadata: dict[str, str] = Field(default_factory=dict)

    parameters: dict[str, float | int | str | bool] = Field(default_factory=dict)

    # -----------------------------------------------------------------

    @computed_field
    @property
    def ffmpeg_name(self) -> str:
        """
        Equivalent FFmpeg xfade transition name.
        """

        mapping = {
            TransitionType.CUT: "fade",
            TransitionType.FADE: "fade",
            TransitionType.DISSOLVE: "fade",
            TransitionType.CROSSFADE: "fade",
            TransitionType.WIPE_LEFT: "wipeleft",
            TransitionType.WIPE_RIGHT: "wiperight",
            TransitionType.WIPE_UP: "wipeup",
            TransitionType.WIPE_DOWN: "wipedown",
            TransitionType.SLIDE_LEFT: "slideleft",
            TransitionType.SLIDE_RIGHT: "slideright",
            TransitionType.SLIDE_UP: "slideup",
            TransitionType.SLIDE_DOWN: "slidedown",
            TransitionType.ZOOM_IN: "zoomin",
            TransitionType.ZOOM_OUT: "zoomout",
            TransitionType.CIRCLE_OPEN: "circleopen",
            TransitionType.CIRCLE_CLOSE: "circleclose",
            TransitionType.RADIAL: "radial",
            TransitionType.PIXELIZE: "pixelize",
            TransitionType.BLUR: "fade",
        }

        return mapping.get(
            self.type,
            "fade",
        )

    # -----------------------------------------------------------------

    @computed_field
    @property
    def is_cut(self) -> bool:

        return self.type == TransitionType.CUT or self.duration <= 0

    # -----------------------------------------------------------------

    @computed_field
    @property
    def is_crossfade(self) -> bool:

        return self.type in {
            TransitionType.CROSSFADE,
            TransitionType.DISSOLVE,
            TransitionType.FADE,
        }

    # -----------------------------------------------------------------

    def set_parameter(
        self,
        name: str,
        value: float | int | str | bool,
    ) -> None:

        self.parameters[name] = value

    # -----------------------------------------------------------------

    def get_parameter(
        self,
        name: str,
        default=None,
    ):

        return self.parameters.get(
            name,
            default,
        )

    # -----------------------------------------------------------------

    def enable(self) -> None:

        self.enabled = True

    # -----------------------------------------------------------------

    def disable(self) -> None:

        self.enabled = False

    # -----------------------------------------------------------------

    def copy_transition(self) -> Transition:
        """
        Duplicate transition with a new ID.
        """

        transition = self.model_copy(
            deep=True,
        )

        transition.id = uuid4().hex

        return transition

    # -----------------------------------------------------------------

    def ffmpeg_arguments(
        self,
        offset: float,
    ) -> str:
        """
        Build the xfade argument string.

        Example

        transition=fade:duration=1:offset=5
        """

        args = f"transition={self.ffmpeg_name}:duration={self.duration}:offset={offset}"

        for key, value in self.parameters.items():
            args += f":{key}={value}"

        return args

    # -----------------------------------------------------------------

    def __repr__(self) -> str:

        return f"Transition(type={self.type.value}, duration={self.duration:.2f}s)"
