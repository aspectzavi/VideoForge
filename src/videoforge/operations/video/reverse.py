"""
Reverse video/audio operation.
"""

from __future__ import annotations

from videoforge.ffmpeg.job import FFmpegJob
from videoforge.operations.base import Operation, OperationContext


class ReverseOperation(Operation):
    """
    Reverse video playback.

    Parameters
    ----------
    video:
        Reverse the video stream.

    audio:
        Reverse the audio stream.
    """

    def __init__(
        self,
        *,
        video: bool = True,
        audio: bool = True,
    ) -> None:
        super().__init__("Reverse")

        if not video and not audio:
            raise ValueError(
                "At least one of 'video' or 'audio' must be enabled."
            )

        self.video = video
        self.audio = audio

    # ------------------------------------------------------------------

    def build_job(
        self,
        context: OperationContext,
    ) -> FFmpegJob:

        video_filters: list[str] = []
        audio_filters: list[str] = []

        if self.video:
            video_filters.append("reverse")

        if self.audio:
            audio_filters.append("areverse")

        return FFmpegJob(
            inputs=[context.input_file],
            output=context.next_output(),
            video_filters=video_filters,
            audio_filters=audio_filters,
        )

    # ------------------------------------------------------------------

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}("
            f"video={self.video}, "
            f"audio={self.audio})"
        )