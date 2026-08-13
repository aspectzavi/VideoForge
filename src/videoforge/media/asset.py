"""
VideoForge Media Asset

Represents a single piece of media that can be used inside a project.

A MediaAsset is immutable metadata describing a file. It does not contain
editing information—that belongs to Clip and Timeline objects.

Examples
--------
Video
Audio
Image
GIF
Image Sequence

This class lazily probes media using FFprobe.
"""

from __future__ import annotations

import hashlib
import mimetypes
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, computed_field

from videoforge.ffmpeg.probe import MediaInfo, probe

AssetType = Literal[
    "video",
    "audio",
    "image",
    "gif",
    "unknown",
]


class MediaAsset(BaseModel):
    """
    Represents a source media file.
    """

    model_config = ConfigDict(
        arbitrary_types_allowed=True,
    )

    # ---------------------------------------------------------
    # Identity
    # ---------------------------------------------------------

    id: str = Field(
        default_factory=lambda: uuid.uuid4().hex,
    )

    # ---------------------------------------------------------
    # Required
    # ---------------------------------------------------------

    path: Path

    # ---------------------------------------------------------
    # Cached probe
    # ---------------------------------------------------------

    media_info: MediaInfo | None = None

    # ---------------------------------------------------------
    # User metadata
    # ---------------------------------------------------------

    label: str | None = None

    tags: list[str] = Field(
        default_factory=list,
    )

    metadata: dict[str, Any] = Field(
        default_factory=dict,
    )

    favorite: bool = False

    rating: int = 0

    notes: str | None = None

    proxy_path: Path | None = None

    created_at: datetime = Field(
        default_factory=datetime.utcnow,
    )

    modified_at: datetime = Field(
        default_factory=datetime.utcnow,
    )

    # =========================================================
    # Construction
    # =========================================================

    @classmethod
    def load(
        cls,
        path: str | Path,
    ) -> MediaAsset:

        path = Path(path)

        return cls(
            path=path,
        )

    # =========================================================
    # Probe
    # =========================================================

    def probe(self) -> MediaInfo:

        if self.media_info is None:
            self.media_info = probe.probe(
                self.path,
            )

        return self.media_info

    def refresh(self) -> None:

        self.media_info = probe.probe(
            self.path,
        )

    # =========================================================
    # File properties
    # =========================================================

    @computed_field
    @property
    def exists(self) -> bool:

        return self.path.exists()

    @computed_field
    @property
    def filename(self) -> str:

        return self.path.name

    @computed_field
    @property
    def stem(self) -> str:

        return self.path.stem

    @computed_field
    @property
    def suffix(self) -> str:

        return self.path.suffix.lower()

    @computed_field
    @property
    def extension(self) -> str:

        return self.suffix.lstrip(".")

    @computed_field
    @property
    def size_bytes(self) -> int:

        if not self.exists:
            return 0

        return self.path.stat().st_size

    @computed_field
    @property
    def size_mb(self) -> float:

        return round(
            self.size_bytes / (1024 * 1024),
            2,
        )

    @computed_field
    @property
    def mime_type(self) -> str | None:

        mime, _ = mimetypes.guess_type(
            self.path,
        )

        return mime

    @computed_field
    @property
    def absolute_path(self) -> Path:

        return self.path.resolve()

    @computed_field
    @property
    def parent(self) -> Path:

        return self.path.parent

    @computed_field
    @property
    def exists_on_disk(self) -> bool:

        return self.absolute_path.exists()

    @computed_field
    @property
    def has_proxy(self) -> bool:

        return self.proxy_path is not None and self.proxy_path.exists()

    @computed_field
    @property
    def file_hash(self) -> str:

        if not self.exists:
            return ""

        h = hashlib.sha1()

        with self.path.open("rb") as f:
            while chunk := f.read(1024 * 1024):
                h.update(chunk)

        return h.hexdigest()

    # =========================================================
    # Type
    # =========================================================

    @computed_field
    @property
    def asset_type(self) -> AssetType:

        ext = self.extension

        if ext in {
            "mp4",
            "mov",
            "avi",
            "mkv",
            "webm",
            "mxf",
            "m4v",
            "flv",
        }:
            return "video"

        if ext in {
            "mp3",
            "wav",
            "aac",
            "ogg",
            "flac",
            "m4a",
        }:
            return "audio"

        if ext in {
            "png",
            "jpg",
            "jpeg",
            "bmp",
            "tif",
            "tiff",
            "webp",
        }:
            return "image"

        if ext == "gif":
            return "gif"

        return "unknown"

    # =========================================================
    # Convenience
    # =========================================================

    @computed_field
    @property
    def duration(self) -> float:

        if self.media_info is None:
            self.probe()

        if self.media_info is None:
            return 0.0

        return self.media_info.duration or 0.0

    @computed_field
    @property
    def width(self) -> int:

        if self.media_info is None:
            self.probe()

        if self.media_info is None:
            return 0

        return self.media_info.width or 0

    @computed_field
    @property
    def height(self) -> int:

        if self.media_info is None:
            self.probe()

        if self.media_info is None:
            return 0

        return self.media_info.height or 0

    @computed_field
    @property
    def fps(self) -> float:

        if self.media_info is None:
            self.probe()

        if self.media_info is None:
            return 0.0

        return self.media_info.fps or 0.0

    @computed_field
    @property
    def resolution(self) -> str:

        if self.media_info is None:
            self.probe()

        if self.media_info is None:
            return ""

        return self.media_info.resolution or ""

    @computed_field
    @property
    def has_audio(self) -> bool:

        if self.media_info is None:
            self.probe()

        if self.media_info is None:
            return False

        return self.media_info.has_audio

    @computed_field
    @property
    def is_vertical(self) -> bool:

        if self.media_info is None:
            self.probe()

        if self.media_info is None:
            return False

        return self.media_info.is_vertical

    @computed_field
    @property
    def aspect_ratio(self) -> float:

        if self.media_info is None:
            self.probe()

        if self.media_info is None:
            return 0.0

        return self.media_info.aspect_ratio or 0.0

    @computed_field
    @property
    def is_video(self) -> bool:
        return self.asset_type == "video"

    @computed_field
    @property
    def is_audio(self) -> bool:
        return self.asset_type == "audio"

    @computed_field
    @property
    def is_image(self) -> bool:
        return self.asset_type == "image"

    @computed_field
    @property
    def is_gif(self) -> bool:
        return self.asset_type == "gif"

    # =========================================================
    # Helpers
    # =========================================================

    def clone(self) -> MediaAsset:
        """
        Create a shallow copy of this asset.
        """
        clone = self.model_copy(deep=True)

        clone.id = uuid.uuid4().hex

        return clone

    def to_dict(self) -> dict:

        return self.model_dump()

    def __str__(self) -> str:

        return str(self.path)

    def __repr__(self) -> str:

        return (
            "MediaAsset("
            f"id='{self.id[:8]}', "
            f"name='{self.filename}', "
            f"type='{self.asset_type}', "
            f"size={self.size_mb:.2f}MB)"
        )

    def set_proxy(
        self,
        path: str | Path,
    ) -> None:

        self.proxy_path = Path(path)

    def remove_proxy(self) -> None:

        self.proxy_path = None

    def add_tag(
        self,
        tag: str,
    ) -> None:

        if tag not in self.tags:
            self.tags.append(tag)

    def remove_tag(
        self,
        tag: str,
    ) -> bool:

        if tag not in self.tags:
            return False

        self.tags.remove(tag)

        return True

    def clear_tags(self) -> None:

        self.tags.clear()

    def set_rating(
        self,
        rating: int,
    ) -> None:

        self.rating = max(
            0,
            min(
                5,
                rating,
            ),
        )

    def favorite_asset(self) -> None:

        self.favorite = True

    def unfavorite_asset(self) -> None:

        self.favorite = False
