"""
Adjust audio volume.
"""

from __future__ import annotations

from videoforge.ffmpeg.job import FFmpegJob
from videoforge.operations.base import Operation, OperationContext


class VolumeOperation(Operation):
    """
    Adjust the audio volume of a media file.

    Parameters
    ----------
    level:
        Volume multiplier. 1.0 leaves the volume unchanged,
        0.5 halves it, 2.0 doubles it.

    Notes
    -----
    This uses FFmpegJob.audio_filters rather than FFmpegJob.volume.
    The command builder emits ``-af`` for audio_filters AND a
    separate ``-af volume=...`` when job.volume is set; FFmpeg only
    honors the last ``-af`` flag on the command line, so combining
    the two would silently drop whichever was emitted first. Using
    audio_filters alone avoids that trap and composes correctly with
    filters added by other operations later in a chain.
    """

    def __init__(
        self,
        level: float,
    ) -> None:
        super().__init__("Volume")

        if level < 0:
            raise ValueError("level must be >= 0.")

        self.level = level

    # ------------------------------------------------------------------

    def build_job(
        self,
        context: OperationContext,
    ) -> FFmpegJob:
        return FFmpegJob(
            inputs=[context.input_file],
            output=context.next_output(),
            audio_filters=[f"volume={self.level}"],
            copy_video=True,
        )

    # ------------------------------------------------------------------

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(level={self.level})"
