"""
Replace a media file's audio track with a different audio file.
"""

from __future__ import annotations

from pathlib import Path

from videoforge.ffmpeg.job import FFmpegJob
from videoforge.operations.base import Operation, OperationContext


class ReplaceAudioOperation(Operation):
    """
    Replace the audio track of a media file with a different audio
    file, discarding the original audio entirely.

    Parameters
    ----------
    audio_file:
        Path to the replacement audio track.

    trim_to_shortest:
        If True, the output is trimmed to the shorter of the video
        and the replacement audio (FFmpeg's -shortest). If False
        (default), the output runs as long as the video stream.
    """

    def __init__(
        self,
        audio_file: Path,
        *,
        trim_to_shortest: bool = False,
    ) -> None:
        super().__init__("Replace Audio")

        self.audio_file = Path(audio_file)
        self.trim_to_shortest = trim_to_shortest

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def prepare(
        self,
        context: OperationContext,
    ) -> None:
        if not self.audio_file.is_file():
            raise FileNotFoundError(
                f"Audio file does not exist: {self.audio_file}"
            )

    # ------------------------------------------------------------------

    def build_job(
        self,
        context: OperationContext,
    ) -> FFmpegJob:
        extra_args = ["-shortest"] if self.trim_to_shortest else []

        return FFmpegJob(
            inputs=[context.input_file, self.audio_file],
            output=context.next_output(),
            map_streams=["0:v?", "1:a:0"],
            copy_video=True,
            extra_args=extra_args,
        )

    # ------------------------------------------------------------------

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}("
            f"audio_file={self.audio_file!s}, "
            f"trim_to_shortest={self.trim_to_shortest})"
        )
