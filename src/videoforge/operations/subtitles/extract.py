
"""
Extract streams from a media file.

Supported extraction:

- Audio
- Video
- Subtitles
"""

from __future__ import annotations

from pathlib import Path

from videoforge.ffmpeg.job import FFmpegJob
from videoforge.operations.base import Operation, OperationContext


class ExtractOperation(Operation):
    """
    Extract a single stream from a media file.

    Exactly one extraction type must be selected.
    """

    def __init__(
        self,
        output: Path,
        *,
        audio: bool = False,
        video: bool = False,
        subtitles: bool = False,
    ) -> None:
        super().__init__("Extract")

        selected = sum(
            (
                audio,
                video,
                subtitles,
            )
        )

        if selected != 1:
            raise ValueError(
                "Exactly one of audio, video or subtitles must be True."
            )

        self.output = Path(output)
        self.audio = audio
        self.video = video
        self.subtitles = subtitles

    # ---------------------------------------------------------
    # Lifecycle
    # ---------------------------------------------------------

    def prepare(
        self,
        context: OperationContext,
    ) -> None:
        """
        Validate the input and output paths before execution.
        """

        if not context.input_file.is_file():
            raise FileNotFoundError(
                f"Input media file does not exist: {context.input_file}"
            )

        if self.output.resolve() == context.input_file.resolve():
            raise ValueError(
                "Extraction output must be different from the input file."
            )

        context.data["extract_type"] = self.extract_type
        context.data["extract_output"] = self.output

    # ---------------------------------------------------------

    @property
    def extract_type(self) -> str:
        """
        Return the selected stream type.
        """

        if self.audio:
            return "audio"

        if self.video:
            return "video"

        return "subtitles"

    # ---------------------------------------------------------

    def build_job(
        self,
        context: OperationContext,
    ) -> FFmpegJob:
        """
        Build the FFmpeg extraction job.
        """

        if self.audio:
            return FFmpegJob(
                inputs=[context.input_file],
                output=self.output,
                map_streams=["0:a:0"],
                copy_audio=True,
            )

        if self.video:
            return FFmpegJob(
                inputs=[context.input_file],
                output=self.output,
                map_streams=["0:v:0"],
                copy_video=True,
            )

        return FFmpegJob(
            inputs=[context.input_file],
            output=self.output,
            map_streams=["0:s:0"],
            subtitle_codec="copy",
        )

    # ---------------------------------------------------------

    def finalize(
        self,
        context: OperationContext,
    ) -> None:
        """
        Store the extracted file as the current operation output.
        """

        context.output_file = self.output
        context.input_file = self.output

    # ---------------------------------------------------------

    def __repr__(self) -> str:
        return (
            "ExtractOperation("
            f"output={self.output!s}, "
            f"type={self.extract_type!r})"
        )
