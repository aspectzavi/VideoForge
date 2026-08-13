"""
Video stabilization operation.
"""

from __future__ import annotations

from pathlib import Path

from videoforge.ffmpeg.job import FFmpegJob
from videoforge.operations.base import Operation, OperationContext


class StabilizeOperation(Operation):
    """
    Stabilize a video using FFmpeg's vidstabtransform filter.

    Parameters
    ----------
    transforms:
        Path to the transform file produced by
        the vidstabdetect filter.

    smoothing:
        Number of frames used for stabilization.

    zoom:
        Automatic zoom to hide border artifacts.
    """

    def __init__(
        self,
        transforms: Path,
        *,
        smoothing: int = 15,
        zoom: float = 0.0,
    ) -> None:
        super().__init__("Stabilize")

        self.transforms = Path(transforms)
        self.smoothing = smoothing
        self.zoom = zoom

    # ------------------------------------------------------------------

    def build_job(
        self,
        context: OperationContext,
    ) -> FFmpegJob:
        filter_expr = (
            "vidstabtransform="
            f"input={self.transforms}:"
            f"smoothing={self.smoothing}:"
            f"zoom={self.zoom}"
        )

        return FFmpegJob(
            inputs=[context.input_file],
            output=context.next_output(),
            video_filters=[filter_expr],
        )

    # ------------------------------------------------------------------

    def __repr__(self) -> str:
        return (
            "StabilizeOperation("
            f"transforms={self.transforms!s}, "
            f"smoothing={self.smoothing}, "
            f"zoom={self.zoom})"
        )