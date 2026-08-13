"""
Resize video operation.
"""

from __future__ import annotations

from videoforge.ffmpeg.job import FFmpegJob
from videoforge.operations.base import Operation, OperationContext


class ResizeOperation(Operation):
    """
    Resize a video.

    Parameters
    ----------
    width:
        Target width.

    height:
        Target height.

    keep_aspect_ratio:
        Preserve the original aspect ratio.
    """

    def __init__(
        self,
        width: int,
        height: int,
        *,
        keep_aspect_ratio: bool = True,
    ) -> None:
        super().__init__("Resize")

        if width <= 0:
            raise ValueError("width must be greater than zero.")

        if height <= 0:
            raise ValueError("height must be greater than zero.")

        self.width = width
        self.height = height
        self.keep_aspect_ratio = keep_aspect_ratio

    # ------------------------------------------------------------------

    def build_job(
        self,
        context: OperationContext,
    ) -> FFmpegJob:
        if self.keep_aspect_ratio:
            filter_expr = (
                f"scale={self.width}:{self.height}:"
                "force_original_aspect_ratio=decrease,"
                f"pad={self.width}:{self.height}:(ow-iw)/2:(oh-ih)/2"
            )
        else:
            filter_expr = f"scale={self.width}:{self.height}"

        return FFmpegJob(
            inputs=[context.input_file],
            output=context.next_output(),
            width=self.width,
            height=self.height,
            keep_aspect_ratio=self.keep_aspect_ratio,
            video_filters=[filter_expr],
        )

    # ------------------------------------------------------------------

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}("
            f"width={self.width}, "
            f"height={self.height}, "
            f"keep_aspect_ratio={self.keep_aspect_ratio})"
        )