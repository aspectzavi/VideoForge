"""
Export a lightweight, lower-resolution editing proxy.
"""

from __future__ import annotations

from pathlib import Path

from videoforge.ffmpeg.job import FFmpegJob
from videoforge.operations.base import Operation, OperationContext


class ProxyOperation(Operation):
    """
    Generate a lower-resolution proxy file suitable for fast editing
    preview, to be swapped back for the full-resolution source at
    final export time.

    Parameters
    ----------
    output:
        Path to the proxy file.

    width:
        Target proxy width in pixels. Height scales to preserve
        aspect ratio (must stay even, hence the -2 divisor).

    video_codec, audio_codec, crf, preset:
        Encoding settings for the proxy. Defaults favor fast encode
        and small file size over quality, appropriate for a
        throwaway editing proxy.
    """

    def __init__(
        self,
        output: Path,
        *,
        width: int = 960,
        video_codec: str = "libx264",
        audio_codec: str = "aac",
        crf: int = 28,
        preset: str = "veryfast",
    ) -> None:
        super().__init__("Export Proxy")

        if width <= 0:
            raise ValueError("width must be greater than zero.")

        self.output = Path(output)
        self.width = width
        self.video_codec = video_codec
        self.audio_codec = audio_codec
        self.crf = crf
        self.preset = preset

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
                "Proxy output must be different from the input file."
            )

    # ------------------------------------------------------------------

    def build_job(
        self,
        context: OperationContext,
    ) -> FFmpegJob:
        return FFmpegJob(
            inputs=[context.input_file],
            output=self.output,
            video_filters=[f"scale={self.width}:-2"],
            video_codec=self.video_codec,
            audio_codec=self.audio_codec,
            crf=self.crf,
            preset=self.preset,
        )

    # ------------------------------------------------------------------

    def finalize(
        self,
        context: OperationContext,
    ) -> None:
        context.data["proxy_file"] = self.output

    # ------------------------------------------------------------------

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}("
            f"output={self.output!s}, "
            f"width={self.width}, "
            f"crf={self.crf}, "
            f"preset={self.preset!r})"
        )
