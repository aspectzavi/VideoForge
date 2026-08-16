"""
Normalize audio loudness.
"""

from __future__ import annotations

from videoforge.ffmpeg.job import FFmpegJob
from videoforge.operations.base import Operation, OperationContext


class NormalizeAudioOperation(Operation):
    """
    Normalize audio loudness using FFmpeg's loudnorm filter
    (EBU R128 single-pass loudness normalization).

    Parameters
    ----------
    target_loudness:
        Integrated loudness target in LUFS. -23.0 is the EBU R128
        broadcast default; streaming platforms often target -14 to -16.

    true_peak:
        Maximum true peak in dBTP.

    loudness_range:
        Target loudness range (LRA) in LU.
    """

    def __init__(
        self,
        *,
        target_loudness: float = -23.0,
        true_peak: float = -2.0,
        loudness_range: float = 7.0,
    ) -> None:
        super().__init__("Normalize Audio")

        if loudness_range <= 0:
            raise ValueError("loudness_range must be greater than zero.")

        self.target_loudness = target_loudness
        self.true_peak = true_peak
        self.loudness_range = loudness_range

    # ------------------------------------------------------------------

    def build_job(
        self,
        context: OperationContext,
    ) -> FFmpegJob:
        filter_expr = (
            "loudnorm="
            f"I={self.target_loudness}:"
            f"TP={self.true_peak}:"
            f"LRA={self.loudness_range}"
        )

        return FFmpegJob(
            inputs=[context.input_file],
            output=context.next_output(),
            audio_filters=[filter_expr],
            copy_video=True,
        )

    # ------------------------------------------------------------------

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}("
            f"target_loudness={self.target_loudness}, "
            f"true_peak={self.true_peak}, "
            f"loudness_range={self.loudness_range})"
        )
