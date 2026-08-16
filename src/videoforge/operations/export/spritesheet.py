"""
Export a grid sprite sheet of thumbnails from a media file.
"""

from __future__ import annotations

from pathlib import Path

from videoforge.ffmpeg.job import FFmpegJob
from videoforge.operations.base import Operation, OperationContext


class SpritesheetOperation(Operation):
    """
    Generate a grid sprite sheet of evenly-spaced thumbnails.

    Parameters
    ----------
    output:
        Path to the output image (e.g. "sheet.jpg", "sheet.png").

    columns, rows:
        Grid dimensions. columns * rows thumbnails are captured.

    interval:
        Seconds between captured frames. If None, FFmpeg's default
        frame selection is used (every frame), which is rarely what
        you want for a sprite sheet spanning a whole video - set this
        explicitly for anything longer than a few seconds.

    thumb_width:
        Width of each individual thumbnail cell in pixels. Height
        scales to preserve aspect ratio.
    """

    def __init__(
        self,
        output: Path,
        *,
        columns: int = 5,
        rows: int = 5,
        interval: float | None = None,
        thumb_width: int = 160,
    ) -> None:
        super().__init__("Export Spritesheet")

        if columns <= 0:
            raise ValueError("columns must be greater than zero.")

        if rows <= 0:
            raise ValueError("rows must be greater than zero.")

        if thumb_width <= 0:
            raise ValueError("thumb_width must be greater than zero.")

        if interval is not None and interval <= 0:
            raise ValueError("interval must be greater than zero.")

        self.output = Path(output)
        self.columns = columns
        self.rows = rows
        self.interval = interval
        self.thumb_width = thumb_width

    # ------------------------------------------------------------------

    @property
    def frame_count(self) -> int:
        return self.columns * self.rows

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
                "Spritesheet output must be different from the input file."
            )

    # ------------------------------------------------------------------

    def build_job(
        self,
        context: OperationContext,
    ) -> FFmpegJob:
        filters: list[str] = []

        if self.interval is not None:
            fps = 1.0 / self.interval
            filters.append(f"fps={fps}")

        filters.append(f"scale={self.thumb_width}:-1")
        filters.append(f"tile={self.columns}x{self.rows}")

        return FFmpegJob(
            inputs=[context.input_file],
            output=self.output,
            video_filters=filters,
            extra_args=["-frames:v", "1"],
        )

    # ------------------------------------------------------------------

    def finalize(
        self,
        context: OperationContext,
    ) -> None:
        context.data["spritesheet_file"] = self.output

    # ------------------------------------------------------------------

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}("
            f"output={self.output!s}, "
            f"columns={self.columns}, "
            f"rows={self.rows}, "
            f"interval={self.interval})"
        )
