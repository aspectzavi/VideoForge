"""
Mix an additional audio track into a media file's existing audio.
"""

from __future__ import annotations

from pathlib import Path

from videoforge.ffmpeg.job import FFmpegJob
from videoforge.operations.base import Operation, OperationContext

_VALID_DURATIONS = frozenset({"longest", "shortest", "first"})


class MixAudioOperation(Operation):
    """
    Mix an external audio track with a media file's existing audio.

    Both tracks are volume-adjusted independently, then combined with
    FFmpeg's amix filter.

    Parameters
    ----------
    audio_file:
        Path to the audio track to mix in.

    mix_volume:
        Volume multiplier applied to audio_file before mixing.

    original_volume:
        Volume multiplier applied to the original audio before mixing.

    duration:
        How the mixed output's duration is determined: "longest",
        "shortest", or "first" (matches amix's duration option).
    """

    def __init__(
        self,
        audio_file: Path,
        *,
        mix_volume: float = 1.0,
        original_volume: float = 1.0,
        duration: str = "longest",
    ) -> None:
        super().__init__("Mix Audio")

        if mix_volume < 0:
            raise ValueError("mix_volume must be >= 0.")

        if original_volume < 0:
            raise ValueError("original_volume must be >= 0.")

        if duration not in _VALID_DURATIONS:
            supported = ", ".join(sorted(_VALID_DURATIONS))
            raise ValueError(f"duration must be one of: {supported}.")

        self.audio_file = Path(audio_file)
        self.mix_volume = mix_volume
        self.original_volume = original_volume
        self.duration = duration

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
        filter_complex = (
            f"[0:a]volume={self.original_volume}[a0];"
            f"[1:a]volume={self.mix_volume}[a1];"
            f"[a0][a1]amix=inputs=2:duration={self.duration}[aout]"
        )

        return FFmpegJob(
            inputs=[context.input_file, self.audio_file],
            output=context.next_output(),
            filter_complex=filter_complex,
            map_streams=["0:v?", "[aout]"],
            copy_video=True,
        )

    # ------------------------------------------------------------------

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}("
            f"audio_file={self.audio_file!s}, "
            f"mix_volume={self.mix_volume}, "
            f"original_volume={self.original_volume}, "
            f"duration={self.duration!r})"
        )
