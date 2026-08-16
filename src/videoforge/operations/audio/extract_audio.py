"""
Extract the audio track from a media file to a standalone audio file.
"""

from __future__ import annotations

from pathlib import Path

from videoforge.ffmpeg.job import FFmpegJob
from videoforge.operations.base import Operation, OperationContext


class ExtractAudioOperation(Operation):
    """
    Extract the audio track from a media file into its own audio file.

    Unlike the generic ExtractOperation in operations/subtitles/extract.py
    (which stream-copies whichever track type is selected), this
    operation supports re-encoding the extracted audio to a specific
    codec, bitrate, and sample rate.

    Parameters
    ----------
    output:
        Path to the extracted audio file.

    audio_codec:
        Target audio codec (e.g. "libmp3lame", "aac"). If None, the
        audio stream is copied without re-encoding.

    bitrate:
        Target audio bitrate (e.g. "192k"). Only meaningful when
        audio_codec is set.

    sample_rate:
        Target sample rate in Hz (e.g. 44100, 48000).
    """

    def __init__(
        self,
        output: Path,
        *,
        audio_codec: str | None = None,
        bitrate: str | None = None,
        sample_rate: int | None = None,
    ) -> None:
        super().__init__("Extract Audio")

        self.output = Path(output)
        self.audio_codec = audio_codec
        self.bitrate = bitrate
        self.sample_rate = sample_rate

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def prepare(
        self,
        context: OperationContext,
    ) -> None:
        if not context.input_file.is_file():
            raise FileNotFoundError(
                f"Input media file does not exist: {context.input_file}"
            )

        if self.output.resolve() == context.input_file.resolve():
            raise ValueError(
                "Extraction output must be different from the input file."
            )

        context.data["extracted_audio_file"] = self.output

    # ------------------------------------------------------------------

    def build_job(
        self,
        context: OperationContext,
    ) -> FFmpegJob:
        return FFmpegJob(
            inputs=[context.input_file],
            output=self.output,
            map_streams=["0:a:0"],
            copy_audio=self.audio_codec is None,
            audio_codec=self.audio_codec,
            audio_bitrate=self.bitrate,
            sample_rate=self.sample_rate,
        )

    # ------------------------------------------------------------------

    def finalize(
        self,
        context: OperationContext,
    ) -> None:
        """
        Store the extracted audio path without altering the pipeline's
        working video file, so later steps keep operating on the video.
        """

        context.data["extracted_audio_file"] = self.output

    # ------------------------------------------------------------------

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}("
            f"output={self.output!s}, "
            f"audio_codec={self.audio_codec!r})"
        )
