"""
Blur video operation.
"""

from __future__ import annotations

from videoforge.ffmpeg.job import FFmpegJob
from videoforge.operations.base import Operation, OperationContext


class BlurOperation(Operation):
    """
    Apply a Gaussian blur to a video.

    Parameters
    ----------
    sigma:
        Blur strength. Typical values are between 0.5 and 20.0.
    """

    def __init__(
        self,
        sigma: float = 5.0,
    ) -> None:
        super().__init__("Blur")

        if sigma <= 0:
            raise ValueError("sigma must be greater than zero.")

        self.sigma = sigma

    # ------------------------------------------------------------------

    def build_job(
        self,
        context: OperationContext,
    ) -> FFmpegJob:
        return FFmpegJob(
            inputs=[context.input_file],
            output=context.next_output(),
            video_filters=[
                f"gblur=sigma={self.sigma}"
            ],
        )

    # ------------------------------------------------------------------

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}("
            f"sigma={self.sigma})"
        )