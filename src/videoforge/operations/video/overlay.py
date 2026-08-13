"""
Overlay another video or image onto a video.
"""

from __future__ import annotations

from pathlib import Path

from videoforge.ffmpeg.job import FFmpegJob
from videoforge.operations.base import Operation, OperationContext


class OverlayOperation(Operation):
    """
    Overlay an image or video on top of another video.

    Parameters
    ----------
    overlay:
        Image/video to overlay.

    x:
        Horizontal position.

    y:
        Vertical position.
    """

    def __init__(
        self,
        overlay: Path,
        *,
        x: int = 0,
        y: int = 0,
    ) -> None:
        super().__init__("Overlay")

        self.overlay = Path(overlay)
        self.x = x
        self.y = y

    # ------------------------------------------------------------------

    def build_job(
        self,
        context: OperationContext,
    ) -> FFmpegJob:
        return FFmpegJob(
            inputs=[
                context.input_file,
                self.overlay,
            ],
            output=context.next_output(),
            filter_complex=f"[0:v][1:v]overlay={self.x}:{self.y}",
            map_streams=[
                "0:a?",
            ],
        )

    # ------------------------------------------------------------------

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}("
            f"overlay={self.overlay!s}, "
            f"x={self.x}, "
            f"y={self.y})"
        )