"""
Color adjustment operation.
"""

from __future__ import annotations

from videoforge.ffmpeg.job import FFmpegJob
from videoforge.operations.base import Operation, OperationContext


class ColorOperation(Operation):
    """
    Adjust video colors using FFmpeg's `eq` filter.

    Parameters
    ----------
    brightness
        Range: -1.0 to 1.0

    contrast
        Range: 0.0 to 2.0

    saturation
        Range: 0.0 to 3.0

    gamma
        Range: 0.1 to 10.0
    """

    def __init__(
        self,
        *,
        brightness: float = 0.0,
        contrast: float = 1.0,
        saturation: float = 1.0,
        gamma: float = 1.0,
    ) -> None:
        super().__init__("Color")

        self.brightness = brightness
        self.contrast = contrast
        self.saturation = saturation
        self.gamma = gamma

    # ---------------------------------------------------------

    def build_job(
        self,
        context: OperationContext,
    ) -> FFmpegJob:
        filter_expr = (
            "eq="
            f"brightness={self.brightness}:"
            f"contrast={self.contrast}:"
            f"saturation={self.saturation}:"
            f"gamma={self.gamma}"
        )

        return FFmpegJob(
            inputs=[context.input_file],
            output=context.next_output(),
            video_filters=[filter_expr],
        )

    # ---------------------------------------------------------

    def __repr__(self) -> str:
        return (
            "ColorOperation("
            f"brightness={self.brightness}, "
            f"contrast={self.contrast}, "
            f"saturation={self.saturation}, "
            f"gamma={self.gamma})"
        )