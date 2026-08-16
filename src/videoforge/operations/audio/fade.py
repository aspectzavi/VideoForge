"""
Fade audio in and/or out.
"""

from __future__ import annotations

from videoforge.ffmpeg.job import FFmpegJob
from videoforge.operations.base import Operation, OperationContext


class AudioFadeOperation(Operation):
    """
    Apply an audio fade-in and/or fade-out using FFmpeg's afade filter.

    Parameters
    ----------
    fade_in:
        Fade-in duration in seconds. 0 disables fade-in.

    fade_out:
        Fade-out duration in seconds. 0 disables fade-out.

    total_duration:
        Total duration of the clip in seconds. Required when
        fade_out > 0, since the fade-out start time is computed as
        total_duration - fade_out.
    """

    def __init__(
        self,
        *,
        fade_in: float = 0.0,
        fade_out: float = 0.0,
        total_duration: float | None = None,
    ) -> None:
        super().__init__("Audio Fade")

        if fade_in < 0:
            raise ValueError("fade_in must be >= 0.")

        if fade_out < 0:
            raise ValueError("fade_out must be >= 0.")

        if fade_in == 0 and fade_out == 0:
            raise ValueError(
                "At least one of fade_in or fade_out must be greater than zero."
            )

        if fade_out > 0 and total_duration is None:
            raise ValueError(
                "total_duration is required to compute the fade-out start time."
            )

        if total_duration is not None and fade_out > total_duration:
            raise ValueError("fade_out cannot be longer than total_duration.")

        self.fade_in = fade_in
        self.fade_out = fade_out
        self.total_duration = total_duration

    # ------------------------------------------------------------------

    def build_job(
        self,
        context: OperationContext,
    ) -> FFmpegJob:
        filters: list[str] = []

        if self.fade_in > 0:
            filters.append(f"afade=t=in:st=0:d={self.fade_in}")

        if self.fade_out > 0:
            start = self.total_duration - self.fade_out
            filters.append(f"afade=t=out:st={start}:d={self.fade_out}")

        return FFmpegJob(
            inputs=[context.input_file],
            output=context.next_output(),
            audio_filters=filters,
            copy_video=True,
        )

    # ------------------------------------------------------------------

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}("
            f"fade_in={self.fade_in}, "
            f"fade_out={self.fade_out})"
        )
