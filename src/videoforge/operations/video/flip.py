"""
Horizontal / vertical flip operation.
"""

from __future__ import annotations

from videoforge.ffmpeg.job import FFmpegJob
from videoforge.operations.base import Operation, OperationContext


class FlipOperation(Operation):
    """
    Flip a video horizontally and/or vertically.

    Examples
    --------
    Horizontal:
        hflip

    Vertical:
        vflip

    Both:
        hflip,vflip
    """

    def __init__(
        self,
        horizontal: bool = True,
        vertical: bool = False,
    ) -> None:
        super().__init__("Flip")

        if not horizontal and not vertical:
            raise ValueError("At least one flip direction must be enabled.")

        self.horizontal = horizontal
        self.vertical = vertical

    # ---------------------------------------------------------

    def build_job(
        self,
        context: OperationContext,
    ) -> FFmpegJob:

        filters: list[str] = []

        if self.horizontal:
            filters.append("hflip")

        if self.vertical:
            filters.append("vflip")

        output = context.next_output()

        return FFmpegJob(
            inputs=[context.input_file],
            output=output,
            video_filters=[",".join(filters)],
        )

    # ---------------------------------------------------------

    def finalize(
        self,
        context: OperationContext,
    ) -> None:
        context.advance()

    # ---------------------------------------------------------

    def __repr__(self) -> str:
        return (
            "FlipOperation("
            f"horizontal={self.horizontal}, "
            f"vertical={self.vertical})"
        )