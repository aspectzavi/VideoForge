"""
Watermark operation.
"""

from __future__ import annotations

from pathlib import Path

from videoforge.ffmpeg.job import FFmpegJob
from videoforge.operations.base import Operation, OperationContext


class WatermarkOperation(Operation):
    """
    Overlay an image watermark onto a video.

    Parameters
    ----------
    watermark:
        Path to the watermark image.

    position:
        One of:
            top-left
            top-right
            bottom-left
            bottom-right
            center

    opacity:
        Watermark opacity (0.0 - 1.0).

    margin:
        Distance from the edge in pixels.
    """

    def __init__(
        self,
        watermark: Path,
        *,
        position: str = "bottom-right",
        opacity: float = 1.0,
        margin: int = 20,
    ) -> None:
        super().__init__("Watermark")

        if not 0.0 <= opacity <= 1.0:
            raise ValueError("opacity must be between 0.0 and 1.0.")

        self.watermark = Path(watermark)
        self.position = position
        self.opacity = opacity
        self.margin = margin

    # ---------------------------------------------------------

    def _overlay_position(self) -> str:
        m = self.margin

        positions = {
            "top-left": f"{m}:{m}",
            "top-right": f"W-w-{m}:{m}",
            "bottom-left": f"{m}:H-h-{m}",
            "bottom-right": f"W-w-{m}:H-h-{m}",
            "center": "(W-w)/2:(H-h)/2",
        }

        try:
            return positions[self.position]
        except KeyError as exc:
            raise ValueError(
                f"Unsupported position: {self.position}"
            ) from exc

    # ---------------------------------------------------------

    def build_job(
        self,
        context: OperationContext,
    ) -> FFmpegJob:
        overlay = self._overlay_position()

        if self.opacity < 1.0:
            filter_complex = (
                f"[1:v]format=rgba,"
                f"colorchannelmixer=aa={self.opacity}"
                f"[wm];"
                f"[0:v][wm]overlay={overlay}"
            )
        else:
            filter_complex = (
                f"[0:v][1:v]overlay={overlay}"
            )

        return FFmpegJob(
            inputs=[
                context.input_file,
                self.watermark,
            ],
            output=context.next_output(),
            filter_complex=filter_complex,
        )

    # ---------------------------------------------------------

    def __repr__(self) -> str:
        return (
            "WatermarkOperation("
            f"watermark={self.watermark!s}, "
            f"position='{self.position}', "
            f"opacity={self.opacity}, "
            f"margin={self.margin})"
        )