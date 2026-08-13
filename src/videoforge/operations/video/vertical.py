"""
Vertical video conversion operation.

Converts landscape videos into a vertical (9:16) format suitable for
TikTok, Instagram Reels, YouTube Shorts, etc.
"""

from __future__ import annotations

from pathlib import Path
from typing import Literal

from videoforge.engine.exceptions import ValidationError
from videoforge.ffmpeg.job import FFmpegJob
from videoforge.ffmpeg.probe import MediaProbe
from videoforge.operations.base import Operation, OperationContext


VerticalMode = Literal[
    "blur",
    "crop",
    "fit",
]

_VALID_MODES: tuple[str, ...] = (
    "blur",
    "crop",
    "fit",
)


class VerticalStep(Operation):
    """
    Convert a video into a vertical 9:16 video.

    Modes
    -----
    blur
        Blurred background with centered original video.

    crop
        Center crop to 9:16.

    fit
        Preserve the entire frame with padding.
    """

    def __init__(
        self,
        output: str | Path,
        mode: VerticalMode = "blur",
        width: int = 1080,
        height: int = 1920,
        video_codec: str = "libx264",
        audio_codec: str = "aac",
        crf: int = 20,
        preset: str = "medium",
    ) -> None:

        super().__init__("Vertical Conversion")

        if mode not in _VALID_MODES:
            raise ValidationError(
                f"Invalid vertical mode {mode!r}. "
                f"Expected one of: {', '.join(_VALID_MODES)}."
            )

        self.output = Path(output)

        self.mode = mode

        self.width = width
        self.height = height

        self.video_codec = video_codec
        self.audio_codec = audio_codec

        self.crf = crf
        self.preset = preset

        self.probe = MediaProbe()

    # ---------------------------------------------------------
    # Prepare
    # ---------------------------------------------------------

    def prepare(
        self,
        context: OperationContext,
    ) -> None:
        """
        Probe the input media before constructing the FFmpeg job.
        """

        context.media_info = self.probe.probe(
            context.input_file,
        )

    # ---------------------------------------------------------
    # Build FFmpeg job
    # ---------------------------------------------------------

    def build_job(
        self,
        context: OperationContext,
    ) -> FFmpegJob:

        if context.media_info is None:
            raise RuntimeError(
                "Media has not been probed."
            )

        context.output_file = self.output

        filter_complex: str | None = None
        video_filters: list[str] = []

        if self.mode == "blur":
            filter_complex = self._build_blur_filter()

        else:
            video_filters = self._build_video_filters()

        return FFmpegJob(
            inputs=[context.input_file],
            output=self.output,
            overwrite=True,
            video_codec=self.video_codec,
            audio_codec=self.audio_codec,
            video_filters=video_filters,
            filter_complex=filter_complex,
            extra_args=[
                "-preset",
                self.preset,
                "-crf",
                str(self.crf),
                "-movflags",
                "+faststart",
            ],
        )

    # ---------------------------------------------------------
    # Finalize
    # ---------------------------------------------------------

    def finalize(
        self,
        context: OperationContext,
    ) -> None:
        """
        Store the generated output in the pipeline context.
        """

        context.output_file = self.output

    # ---------------------------------------------------------
    # Standard video filters
    # ---------------------------------------------------------

    def _build_video_filters(self) -> list[str]:

        if self.mode == "crop":
            return [
                f"scale=-2:{self.height},"
                f"crop={self.width}:{self.height}"
            ]

        if self.mode == "fit":
            return [
                (
                    f"scale={self.width}:{self.height}:"
                    "force_original_aspect_ratio=decrease,"
                    f"pad={self.width}:{self.height}:"
                    "(ow-iw)/2:(oh-ih)/2"
                )
            ]

        return []

    # ---------------------------------------------------------
    # Blur background
    # ---------------------------------------------------------

    def _build_blur_filter(self) -> str:
        """
        Build a filter_complex graph for blurred-background mode.
        """

        return (
            "[0:v]"
            f"scale={self.width}:{self.height},"
            "boxblur=30:5"
            "[bg];"
            "[0:v]"
            f"scale={self.width}:{self.height}:"
            "force_original_aspect_ratio=decrease"
            "[fg];"
            "[bg][fg]"
            "overlay=(W-w)/2:(H-h)/2"
        )


# Backwards-compatible public name.
#
# Existing code using VerticalOperation continues to work,
# while the pipeline/test API can use VerticalStep.

VerticalOperation = VerticalStep