"""
FFmpeg executable discovery and validation.
"""

from __future__ import annotations

import shutil
from pathlib import Path

from pydantic import BaseModel

from videoforge.engine.exceptions import (
    FFmpegNotFoundError,
    FFprobeNotFoundError,
)


class FFmpegBinaries(BaseModel):
    ffmpeg: Path
    ffprobe: Path


def locate_binaries() -> FFmpegBinaries:
    """
    Locate ffmpeg and ffprobe executables from PATH.
    """

    ffmpeg = shutil.which("ffmpeg")
    ffprobe = shutil.which("ffprobe")

    if ffmpeg is None:
        raise FFmpegNotFoundError("FFmpeg executable could not be found.")

    if ffprobe is None:
        raise FFprobeNotFoundError("FFprobe executable could not be found.")

    return FFmpegBinaries(
        ffmpeg=Path(ffmpeg),
        ffprobe=Path(ffprobe),
    )


BINARIES = locate_binaries()
