"""
Remove audio from a media file.
"""

from __future__ import annotations

from videoforge.ffmpeg.job import FFmpegJob
from videoforge.operations.base import Operation, OperationContext


class MuteOperation(Operation):
    """
    Remove all audio streams from a media file.

    The video stream is stream-copied (not re-encoded) since only the
    audio is being dropped.
    """

    def __init__(self) -> None:
        super().__init__("Mute")

    # ------------------------------------------------------------------

    def build_job(
        self,
        context: OperationContext,
    ) -> FFmpegJob:
        return FFmpegJob(
            inputs=[context.input_file],
            output=context.next_output(),
            copy_video=True,
            extra_args=["-an"],
        )

    # ------------------------------------------------------------------

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}()"
