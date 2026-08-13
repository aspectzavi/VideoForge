
"""
Subtitle operations for VideoForge.

This package provides operations for generating, converting,
extracting, embedding, and burning subtitle tracks.
"""

from __future__ import annotations

from videoforge.operations.subtitles.burn_in import (
    BurnInSubtitlesOperation,
)
from videoforge.operations.subtitles.captions import (
    CaptionGenerationOperation,
)
from videoforge.operations.subtitles.convert import (
    ConvertSubtitlesOperation,
)
from videoforge.operations.subtitles.embed import (
    EmbedSubtitlesOperation,
)
from videoforge.operations.subtitles.extract import (
    ExtractOperation,
)

__all__ = [
    "BurnInSubtitlesOperation",
    "CaptionGenerationOperation",
    "ConvertSubtitlesOperation",
    "EmbedSubtitlesOperation",
    "ExtractOperation",
]
