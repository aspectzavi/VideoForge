"""
Crop video operation.
"""

from __future__ import annotations

from pydantic import Field

from videoforge.ffmpeg.job import FFmpegJob
from videoforge.operations.base import Operation, OperationContext


class CropOperation(Operation):
    """
    Crop a video.

    Example:
        CropOperation(
            x=100,
            y=50,
            width=1280,
            height=720,
        )
    """

    x: int = Field(default=0)
    y: int = Field(default=0)
    width: int
    height: int

    def __init__(
        self,
        width: int,
        height: int,
        x: int = 0,
        y: int = 0,
    ) -> None:
        super().__init__()

        if width <= 0:
            raise ValueError("width must be > 0")

        if height <= 0:
            raise ValueError("height must be > 0")

        self.width = width
        self.height = height
        self.x = x
        self.y = y

    # ---------------------------------------------------------

    def build_job(
        self,
        context: OperationContext,
    ) -> FFmpegJob:
        output = (
            context.output_file
            or context.input_file.with_stem(f"{context.input_file.stem}_crop")
        )

        return FFmpegJob(
            inputs=[context.input_file],
            output=output,
            video_filters=[
                f"crop={self.width}:{self.height}:{self.x}:{self.y}"
            ],
        )

    # ---------------------------------------------------------

    def finalize(
        self,
        context: OperationContext,
    ) -> None:
        if context.output_file is not None:
            context.input_file = context.output_file