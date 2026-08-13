
"""
Embed a subtitle track into a media file without burning it into the video.
"""

from __future__ import annotations

from pathlib import Path

from videoforge.ffmpeg.job import FFmpegJob
from videoforge.operations.base import Operation, OperationContext


class EmbedSubtitlesOperation(Operation):
    """
    Embed an external subtitle file as a selectable subtitle stream.

    Unlike BurnInSubtitlesOperation, this operation does not render
    subtitle text into the video frames. The resulting subtitle track
    can be enabled or disabled by the media player.

    Parameters
    ----------
    subtitles:
        Path to the subtitle file.

    output:
        Output media file.

    language:
        Optional ISO language code for the subtitle stream.

    title:
        Optional human-readable subtitle track title.
    """

    def __init__(
        self,
        subtitles: Path,
        output: Path,
        *,
        language: str | None = None,
        title: str | None = None,
    ) -> None:
        super().__init__("Embed Subtitles")

        self.subtitles = Path(subtitles)
        self.output = Path(output)
        self.language = language
        self.title = title

    # ---------------------------------------------------------
    # Lifecycle
    # ---------------------------------------------------------

    def prepare(
        self,
        context: OperationContext,
    ) -> None:
        """
        Validate the video and subtitle inputs before execution.
        """

        if not context.input_file.is_file():
            raise FileNotFoundError(
                f"Input media file does not exist: {context.input_file}"
            )

        if not self.subtitles.is_file():
            raise FileNotFoundError(
                f"Subtitle file does not exist: {self.subtitles}"
            )

        if self.output.resolve() == context.input_file.resolve():
            raise ValueError(
                "Embed output must be different from the input media file."
            )

        if self.language is not None:
            self.language = self.language.strip().lower()

            if not self.language:
                self.language = None

        if self.title is not None:
            self.title = self.title.strip()

            if not self.title:
                self.title = None

        context.data["subtitle_file"] = self.subtitles
        context.data["subtitle_language"] = self.language
        context.data["subtitle_title"] = self.title

    # ---------------------------------------------------------

    def build_job(
        self,
        context: OperationContext,
    ) -> FFmpegJob:
        """
        Build an FFmpeg job that copies the existing video/audio
        streams and adds the external subtitle stream.
        """

        metadata: dict[str, str] = {}

        if self.language:
            metadata["s:s:0:language"] = self.language

        if self.title:
            metadata["s:s:0:title"] = self.title

        return FFmpegJob(
            inputs=[
                context.input_file,
                self.subtitles,
            ],
            output=self.output,
            map_streams=[
                "0:v?",
                "0:a?",
                "1:0",
            ],
            copy_video=True,
            copy_audio=True,
            subtitle_codec="copy",
            metadata=metadata,
        )

    # ---------------------------------------------------------

    def finalize(
        self,
        context: OperationContext,
    ) -> None:
        """
        Make the embedded-subtitle media file the current pipeline file.
        """

        context.output_file = self.output
        context.input_file = self.output

    # ---------------------------------------------------------

    def __repr__(self) -> str:
        return (
            "EmbedSubtitlesOperation("
            f"subtitles={self.subtitles!s}, "
            f"output={self.output!s}, "
            f"language={self.language!r}, "
            f"title={self.title!r})"
        )
