
"""
Generate subtitle files from transcription segments.
"""

from __future__ import annotations

from pathlib import Path

from videoforge.operations.base import Operation, OperationContext


class CaptionGenerationOperation(Operation):
    """
    Generate subtitle files from transcription segments.

    This operation does not invoke FFmpeg. Instead, it signals the
    transcription/captioning subsystem to create a subtitle file.

    The generated subtitle path is stored in
    ``context.data["subtitle_file"]``.
    """

    SUPPORTED_FORMATS = frozenset(
        {
            "srt",
            "vtt",
            "ass",
        }
    )

    def __init__(
        self,
        *,
        language: str | None = None,
        format: str = "srt",
    ) -> None:
        super().__init__("Generate Captions")

        subtitle_format = format.lower().strip()

        if subtitle_format not in self.SUPPORTED_FORMATS:
            supported = ", ".join(
                sorted(self.SUPPORTED_FORMATS)
            )

            raise ValueError(
                f"format must be one of: {supported}."
            )

        self.language = (
            language.strip()
            if language is not None
            else None
        )

        self.format = subtitle_format

    # ------------------------------------------------------------------

    def prepare(
        self,
        context: OperationContext,
    ) -> None:
        """
        Prepare the expected subtitle output path and caption metadata.

        The actual transcription and subtitle generation are handled by
        the AI/transcription subsystem.
        """

        subtitle_file = context.input_file.with_suffix(
            f".{self.format}"
        )

        context.data["subtitle_file"] = subtitle_file
        context.data["subtitle_language"] = self.language
        context.data["subtitle_format"] = self.format

    # ------------------------------------------------------------------

    def build_job(
        self,
        context: OperationContext,
    ) -> None:
        """
        Caption generation is handled outside FFmpeg.

        The pipeline therefore receives no FFmpeg job.
        """

        return None

    # ------------------------------------------------------------------

    def finalize(
        self,
        context: OperationContext,
    ) -> None:
        """
        Preserve the generated subtitle information.

        This operation does not replace the current media input because
        its output is a subtitle file rather than a new video/media file.
        """

        subtitle_file = context.data.get("subtitle_file")

        if isinstance(subtitle_file, Path):
            context.data["subtitle_file"] = subtitle_file

    # ------------------------------------------------------------------

    @property
    def subtitle_file(self) -> Path | None:
        """
        Return the expected subtitle path when available.

        The actual path is determined from the pipeline input during
        ``prepare()``.
        """

        return None

    # ------------------------------------------------------------------

    def __repr__(self) -> str:
        return (
            "CaptionGenerationOperation("
            f"language={self.language!r}, "
            f"format={self.format!r})"
        )
