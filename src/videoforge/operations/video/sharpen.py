"""
Sharpen video operation.
"""

from __future__ import annotations

from videoforge.ffmpeg.job import FFmpegJob
from videoforge.operations.base import Operation, OperationContext


class SharpenOperation(Operation):
    """
    Sharpen a video using FFmpeg's unsharp filter.

    Parameters
    ----------
    amount:
        Sharpen intensity. Typical values are between
        0.5 and 5.0.
    """

    def __init__(
        self,
        amount: float = 1.5,
    ) -> None:
        super().__init__("Sharpen")

        if amount <= 0:
            raise ValueError("amount must be greater than zero.")

        self.amount = amount

    # ------------------------------------------------------------------

    def build_job(
        self,
        context: OperationContext,
    ) -> FFmpegJob:
        return FFmpegJob(
            inputs=[context.input_file],
            output=context.next_output(),
            video_filters=[
                (
                    "unsharp="
                    f"5:5:{self.amount}:"
                    f"5:5:0.0"
                )
            ],
        )

    # ------------------------------------------------------------------

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}("
            f"amount={self.amount})"
        )