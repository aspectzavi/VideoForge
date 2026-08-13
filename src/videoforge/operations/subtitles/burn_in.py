
"""
Burn subtitles into a video.
"""

from __future__ import annotations

from pathlib import Path

from videoforge.ffmpeg.job import FFmpegJob
from videoforge.operations.base import Operation, OperationContext


class BurnInSubtitlesOperation(Operation):
    """
    Burn subtitles directly into a video.

    Supports SRT, ASS, and SSA subtitle files.

    Parameters
    ----------
    subtitles:
        Subtitle file.

    output:
        Output video file.

    style:
        Optional ASS force_style string.
    """

    def __init__(
        self,
        subtitles: Path,
        output: Path,
        *,
        style: str | None = None,
    ) -> None:
        super().__init__("Burn Subtitles")

        self.subtitles = Path(subtitles)
        self.output = Path(output)
        self.style = style

    # ---------------------------------------------------------
    # Lifecycle
    # ---------------------------------------------------------

    def prepare(
        self,
        context: OperationContext,
    ) -> None:
        """
        Validate the subtitle input before FFmpeg execution.
        """

        if not self.subtitles.is_file():
            raise FileNotFoundError(
                f"Subtitle file does not exist: {self.subtitles}"
            )

        if not context.input_file.is_file():
            raise FileNotFoundError(
                f"Input video does not exist: {context.input_file}"
            )

        if self.output.resolve() == context.input_file.resolve():
            raise ValueError(
                "Burn-in output must be different from the input video."
            )

        context.data["subtitle_file"] = self.subtitles
        context.data["subtitle_style"] = self.style

    # ---------------------------------------------------------

    @staticmethod
    def _escape_subtitle_path(
        path: Path,
    ) -> str:
        """
        Escape a subtitle path for FFmpeg's subtitles filter.

        FFmpeg filter expressions treat characters such as ':',
        backslashes, quotes, and apostrophes specially.
        """

        value = path.resolve().as_posix()

        value = value.replace("\\", r"\\")
        value = value.replace(":", r"\:")
        value = value.replace("'", r"\'")

        return value

    # ---------------------------------------------------------

    def build_job(
        self,
        context: OperationContext,
    ) -> FFmpegJob:
        """
        Build the FFmpeg subtitle burn-in job.
        """

        subtitle_path = self._escape_subtitle_path(
            self.subtitles
        )

        filter_expr = f"subtitles='{subtitle_path}'"

        if self.style:
            filter_expr = (
                f"{filter_expr}:"
                f"force_style='{self.style}'"
            )

        return FFmpegJob(
            inputs=[context.input_file],
            output=self.output,
            video_filters=[filter_expr],
        )

    # ---------------------------------------------------------

    def finalize(
        self,
        context: OperationContext,
    ) -> None:
        """
        Make the burned-in video the current pipeline output/input.
        """

        context.output_file = self.output
        context.input_file = self.output

    # ---------------------------------------------------------

    def __repr__(self) -> str:
        return (
            "BurnInSubtitlesOperation("
            f"subtitles={self.subtitles!s}, "
            f"output={self.output!s}, "
            f"style={self.style!r})"
        )
