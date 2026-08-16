"""
Export an animated GIF from a media file.
"""

from __future__ import annotations

from pathlib import Path

from videoforge.ffmpeg.job import FFmpegJob
from videoforge.operations.base import Operation, OperationContext


class GifOperation(Operation):
    """
    Export a section of a media file as an animated GIF.

    Parameters
    ----------
    output:
        Path to the output GIF file.

    start:
        Start timestamp in seconds.

    duration:
        Duration in seconds. If None, exports to the end of the input.

    fps:
        Frame rate of the resulting GIF.

    width:
        Output width in pixels. Height scales to preserve aspect ratio.
    """

    def __init__(
        self,
        output: Path,
        *,
        start: float = 0.0,
        duration: float | None = None,
        fps: int = 10,
        width: int = 480,
    ) -> None:
        super().__init__("Export GIF")

        if start < 0:
            raise ValueError("start must be >= 0.")

        if duration is not None and duration <= 0:
            raise ValueError("duration must be greater than zero.")

        if fps <= 0:
            raise ValueError("fps must be greater than zero.")

        if width <= 0:
            raise ValueError("width must be greater than zero.")

        self.output = Path(output)
        self.start = start
        self.duration = duration
        self.fps = fps
        self.width = width

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def prepare(
        self,
        context: OperationContext,
    ) -> None:
        if not context.input_file.is_file():
            raise FileNotFoundError(
                f"Input media file does not exist: {context.input_file}"
            )

        if self.output.resolve() == context.input_file.resolve():
            raise ValueError(
                "GIF output must be different from the input file."
            )

    # ------------------------------------------------------------------

    def build_job(
        self,
        context: OperationContext,
    ) -> FFmpegJob:
        filter_expr = f"fps={self.fps},scale={self.width}:-1:flags=lanczos"

        return FFmpegJob(
            inputs=[context.input_file],
            output=self.output,
            start_time=self.start,
            duration=self.duration,
            video_filters=[filter_expr],
            extra_args=["-loop", "0"],
        )

    # ------------------------------------------------------------------

    def finalize(
        self,
        context: OperationContext,
    ) -> None:
        context.data["gif_file"] = self.output

    # ------------------------------------------------------------------

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}("
            f"output={self.output!s}, "
            f"start={self.start}, "
            f"duration={self.duration}, "
            f"fps={self.fps}, "
            f"width={self.width})"
        )
