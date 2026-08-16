"""
Export a single-frame thumbnail image from a media file.
"""

from __future__ import annotations

from pathlib import Path

from videoforge.ffmpeg.job import FFmpegJob
from videoforge.operations.base import Operation, OperationContext


class ThumbnailOperation(Operation):
    """
    Extract a single frame from a media file as a thumbnail image.

    Parameters
    ----------
    output:
        Path to the thumbnail image (e.g. "thumb.jpg", "thumb.png").

    time:
        Timestamp in seconds to capture the frame at.

    width, height:
        Optional output dimensions. Either may be omitted (or left as
        None) to let FFmpeg preserve the aspect ratio for that axis.
    """

    def __init__(
        self,
        output: Path,
        *,
        time: float = 0.0,
        width: int | None = None,
        height: int | None = None,
    ) -> None:
        super().__init__("Thumbnail")

        if time < 0:
            raise ValueError("time must be >= 0.")

        self.output = Path(output)
        self.time = time
        self.width = width
        self.height = height

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
                "Thumbnail output must be different from the input file."
            )

    # ------------------------------------------------------------------

    def build_job(
        self,
        context: OperationContext,
    ) -> FFmpegJob:
        video_filters: list[str] = []

        if self.width is not None or self.height is not None:
            w = self.width if self.width is not None else -1
            h = self.height if self.height is not None else -1
            video_filters.append(f"scale={w}:{h}")

        # NOTE: FFmpegJob.thumbnail_time exists as a declared field but
        # FFmpegCommandBuilder never reads it (confirmed by inspecting
        # command.py) - it's a dead field. The actual seek is done via
        # start_time, and a single frame is captured with extra_args.
        return FFmpegJob(
            inputs=[context.input_file],
            output=self.output,
            start_time=self.time,
            video_filters=video_filters,
            extra_args=["-frames:v", "1"],
        )

    # ------------------------------------------------------------------

    def finalize(
        self,
        context: OperationContext,
    ) -> None:
        context.data["thumbnail_file"] = self.output

    # ------------------------------------------------------------------

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}("
            f"output={self.output!s}, "
            f"time={self.time})"
        )
