
"""
Convert subtitle files between supported subtitle formats.
"""

from __future__ import annotations

from pathlib import Path

from videoforge.ffmpeg.job import FFmpegJob
from videoforge.operations.base import Operation, OperationContext


class ConvertSubtitlesOperation(Operation):
    """
    Convert a subtitle file between supported subtitle formats.

    Supported formats:
        - srt
        - vtt
        - ass
        - ssa
    """

    SUPPORTED_FORMATS = frozenset(
        {
            "srt",
            "vtt",
            "ass",
            "ssa",
        }
    )

    def __init__(
        self,
        output: Path,
        *,
        input_format: str | None = None,
        output_format: str | None = None,
    ) -> None:
        super().__init__("Convert Subtitles")

        self.output = Path(output)

        self.input_format = (
            input_format.lower()
            if input_format is not None
            else None
        )

        self.output_format = (
            output_format.lower()
            if output_format is not None
            else self.output.suffix.lstrip(".").lower()
        )

        if self.input_format is not None:
            self._validate_format(
                self.input_format,
                "input_format",
            )

        self._validate_format(
            self.output_format,
            "output_format",
        )

    # ---------------------------------------------------------
    # Validation
    # ---------------------------------------------------------

    @classmethod
    def _validate_format(
        cls,
        subtitle_format: str,
        name: str,
    ) -> None:
        if subtitle_format not in cls.SUPPORTED_FORMATS:
            supported = ", ".join(
                sorted(cls.SUPPORTED_FORMATS)
            )

            raise ValueError(
                f"{name} must be one of: {supported}."
            )

    # ---------------------------------------------------------
    # Lifecycle
    # ---------------------------------------------------------

    def prepare(
        self,
        context: OperationContext,
    ) -> None:
        """
        Determine the input subtitle format and store metadata
        in the shared operation context.
        """

        if self.input_format is None:
            suffix = (
                context.input_file
                .suffix
                .lstrip(".")
                .lower()
            )

            if suffix in self.SUPPORTED_FORMATS:
                self.input_format = suffix

        if self.input_format is None:
            raise ValueError(
                "Could not determine the input subtitle format. "
                "Specify input_format explicitly."
            )

        if self.input_format == self.output_format:
            raise ValueError(
                "Input and output subtitle formats are identical. "
                "No conversion is required."
            )

        context.data["subtitle_input_format"] = (
            self.input_format
        )

        context.data["subtitle_output_format"] = (
            self.output_format
        )

    # ---------------------------------------------------------

    def build_job(
        self,
        context: OperationContext,
    ) -> FFmpegJob:
        """
        Build an FFmpeg subtitle conversion job.

        FFmpeg determines the subtitle encoder from the output
        container/extension. The subtitle stream is mapped explicitly.
        """

        return FFmpegJob(
            inputs=[context.input_file],
            output=self.output,
            map_streams=["0:0"],
        )

    # ---------------------------------------------------------

    def finalize(
        self,
        context: OperationContext,
    ) -> None:
        """
        Make the converted subtitle file the current pipeline input.
        """

        context.output_file = self.output
        context.input_file = self.output

    # ---------------------------------------------------------

    @property
    def output_suffix(self) -> str:
        """Return the normalized output suffix."""

        return f".{self.output_format}"

    # ---------------------------------------------------------

    def __repr__(self) -> str:
        return (
            "ConvertSubtitlesOperation("
            f"output={self.output!s}, "
            f"input_format={self.input_format!r}, "
            f"output_format={self.output_format!r})"
        )

