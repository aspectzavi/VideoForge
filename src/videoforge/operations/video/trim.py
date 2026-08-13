"""
Trim video operation.
"""

from __future__ import annotations

from videoforge.ffmpeg.job import FFmpegJob
from videoforge.operations.base import Operation, OperationContext


class TrimOperation(Operation):
    """
    Trim a section from a media file.

    Parameters
    ----------
    start:
        Start time in seconds.

    end:
        End time in seconds.

    Examples
    --------
    TrimOperation(5, 15)

    Keeps media from 5s to 15s.
    """

    def __init__(
        self,
        start: float,
        end: float,
    ) -> None:
        super().__init__("Trim")

        if start < 0:
            raise ValueError("start must be >= 0.")

        if end <= start:
            raise ValueError("end must be greater than start.")

        self.start = start
        self.end = end

    # ------------------------------------------------------------------

    @property
    def duration(self) -> float:
        return self.end - self.start

    # ------------------------------------------------------------------

    def build_job(
        self,
        context: OperationContext,
    ) -> FFmpegJob:
        return FFmpegJob(
            inputs=[context.input_file],
            output=context.next_output(),
            start_time=self.start,
            duration=self.duration,
        )

    # ------------------------------------------------------------------

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}("
            f"start={self.start}, "
            f"end={self.end})"
        )