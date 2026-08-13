"""
Rotate video operation.
"""

from __future__ import annotations

from videoforge.ffmpeg.job import FFmpegJob
from videoforge.operations.base import Operation, OperationContext


class RotateOperation(Operation):
    """
    Rotate a video by 90°, 180°, or 270°.

    Examples
    --------
    RotateOperation(90)
    RotateOperation(180)
    RotateOperation(270)
    """

    def __init__(
        self,
        angle: int,
    ) -> None:
        super().__init__("Rotate")

        if angle not in (90, 180, 270):
            raise ValueError("Rotation angle must be one of 90, 180, or 270 degrees.")

        self.angle = angle

    # ------------------------------------------------------------------

    def build_job(
        self,
        context: OperationContext,
    ) -> FFmpegJob:

        if self.angle == 90:
            filters = ["transpose=1"]

        elif self.angle == 180:
            filters = ["transpose=2,transpose=2"]

        else:  # 270
            filters = ["transpose=2"]

        return FFmpegJob(
            inputs=[context.input_file],
            output=context.next_output(),
            video_filters=filters,
        )

    # ------------------------------------------------------------------

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}("
            f"angle={self.angle})"
        )
