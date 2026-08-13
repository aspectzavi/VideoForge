"""
Playback speed operation.
"""

from __future__ import annotations

from videoforge.ffmpeg.job import FFmpegJob
from videoforge.operations.base import Operation, OperationContext


class SpeedOperation(Operation):
    """
    Change playback speed.

    Parameters
    ----------
    speed:
        Playback speed multiplier.

        Examples
        --------
        0.5  -> half speed
        1.0  -> normal
        2.0  -> double speed
        4.0  -> four times faster
    """

    def __init__(
        self,
        speed: float,
    ) -> None:
        super().__init__("Speed")

        if speed <= 0:
            raise ValueError("speed must be greater than zero.")

        self.speed = speed

    # ------------------------------------------------------------------

    @staticmethod
    def _audio_filter(speed: float) -> str:
        """
        Build an atempo chain.

        FFmpeg supports atempo values between 0.5 and 2.0.
        """

        filters: list[str] = []

        value = speed

        while value > 2.0:
            filters.append("atempo=2.0")
            value /= 2.0

        while value < 0.5:
            filters.append("atempo=0.5")
            value *= 2.0

        filters.append(f"atempo={value:.6f}".rstrip("0").rstrip("."))

        return ",".join(filters)

    # ------------------------------------------------------------------

    def build_job(
        self,
        context: OperationContext,
    ) -> FFmpegJob:
        video_filter = f"setpts=PTS/{self.speed}"

        audio_filter = self._audio_filter(self.speed)

        return FFmpegJob(
            inputs=[context.input_file],
            output=context.next_output(),
            video_filters=[video_filter],
            audio_filters=[audio_filter],
        )

    # ------------------------------------------------------------------

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}("
            f"speed={self.speed})"
        )