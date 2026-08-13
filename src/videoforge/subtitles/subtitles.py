"""
Core subtitle models.
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, Field, computed_field

# ==========================================================
# Subtitle Format
# ==========================================================


class SubtitleFormat(StrEnum):
    SRT = "srt"
    VTT = "vtt"
    ASS = "ass"
    SSA = "ssa"


# ==========================================================
# Subtitle Cue
# ==========================================================


class SubtitleCue(BaseModel):
    """
    A single subtitle entry.
    """

    start: float

    end: float

    text: str

    speaker: str | None = None

    confidence: float | None = None

    words: list[str] = Field(default_factory=list)

    @computed_field
    @property
    def duration(self) -> float:
        return max(0.0, self.end - self.start)


# ==========================================================
# Subtitle Track
# ==========================================================


class SubtitleTrack(BaseModel):
    """
    Represents one subtitle track.
    """

    language: str = "en"

    title: str | None = None

    format: SubtitleFormat = SubtitleFormat.SRT

    cues: list[SubtitleCue] = Field(default_factory=list)

    default: bool = True

    forced: bool = False

    # ------------------------------------------------------

    @computed_field
    @property
    def cue_count(self) -> int:
        return len(self.cues)

    @computed_field
    @property
    def duration(self) -> float:
        if not self.cues:
            return 0.0

        return self.cues[-1].end

    # ------------------------------------------------------

    def add(
        self,
        cue: SubtitleCue,
    ) -> None:
        self.cues.append(cue)

    def clear(self) -> None:
        self.cues.clear()

    def sort(self) -> None:
        self.cues.sort(key=lambda cue: cue.start)


# ==========================================================
# Subtitle Style
# ==========================================================


class SubtitleStyle(BaseModel):
    """
    Rendering style used for ASS generation.
    """

    font: str = "Arial"

    font_size: int = 36

    bold: bool = False

    italic: bool = False

    primary_color: str = "&H00FFFFFF"

    outline_color: str = "&H00000000"

    outline: int = 2

    shadow: int = 1

    alignment: int = 2

    margin_left: int = 40

    margin_right: int = 40

    margin_vertical: int = 30


# ==========================================================
# Subtitle Document
# ==========================================================


class SubtitleDocument(BaseModel):
    """
    Complete subtitle document.
    """

    track: SubtitleTrack

    style: SubtitleStyle = Field(default_factory=SubtitleStyle)

    metadata: dict[str, str] = Field(default_factory=dict)