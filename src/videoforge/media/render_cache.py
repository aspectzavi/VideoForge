"""
VideoForge Render Cache

Temporary cache used by the renderer.

Nothing stored here is considered permanent project data.
Everything can safely be regenerated.

Caches include:

- Timeline preview frames
- Thumbnail images
- Audio waveforms
- Proxy media
- Preview renders
- GPU resources
- Filter cache
- Subtitle cache
- Overlay cache
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, computed_field

# ==========================================================
# Cache Entry
# ==========================================================


class CacheEntry(BaseModel):
    """
    Generic cache entry.
    """

    model_config = ConfigDict(
        arbitrary_types_allowed=True,
    )

    path: Path

    created_at: datetime = Field(
        default_factory=datetime.utcnow,
    )

    modified_at: datetime = Field(
        default_factory=datetime.utcnow,
    )

    metadata: dict[str, Any] = Field(
        default_factory=dict,
    )

    # ------------------------------------------------------

    @computed_field
    @property
    def exists(self) -> bool:
        return self.path.exists()

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


# ==========================================================
# Render Cache
# ==========================================================


class RenderCache(BaseModel):
    """
    Runtime rendering cache.

    Entirely disposable.
    """

    model_config = ConfigDict(
        arbitrary_types_allowed=True,
    )

    # ------------------------------------------------------
    # Image Cache
    # ------------------------------------------------------

    thumbnails: dict[str, CacheEntry] = Field(
        default_factory=dict,
    )

    preview_frames: dict[int, CacheEntry] = Field(
        default_factory=dict,
    )

    rendered_frames: dict[int, CacheEntry] = Field(
        default_factory=dict,
    )

    # ------------------------------------------------------
    # Audio Cache
    # ------------------------------------------------------

    waveforms: dict[str, CacheEntry] = Field(
        default_factory=dict,
    )

    audio_cache: dict[str, CacheEntry] = Field(
        default_factory=dict,
    )

    # ------------------------------------------------------
    # Proxy Cache
    # ------------------------------------------------------

    proxies: dict[str, CacheEntry] = Field(
        default_factory=dict,
    )

    # ------------------------------------------------------
    # Preview Renders
    # ------------------------------------------------------

    preview_videos: dict[str, CacheEntry] = Field(
        default_factory=dict,
    )

    preview_audio: dict[str, CacheEntry] = Field(
        default_factory=dict,
    )

    # ------------------------------------------------------
    # Subtitle Cache
    # ------------------------------------------------------

    subtitles: dict[str, CacheEntry] = Field(
        default_factory=dict,
    )

    # ------------------------------------------------------
    # Overlay Cache
    # ------------------------------------------------------

    overlays: dict[str, CacheEntry] = Field(
        default_factory=dict,
    )

    # ------------------------------------------------------
    # Filter Cache
    # ------------------------------------------------------

    filters: dict[str, Any] = Field(
        default_factory=dict,
    )

    # ------------------------------------------------------
    # GPU Cache
    # ------------------------------------------------------

    gpu: dict[str, Any] = Field(
        default_factory=dict,
    )

    # ------------------------------------------------------
    # Misc
    # ------------------------------------------------------

    metadata: dict[str, Any] = Field(
        default_factory=dict,
    )

    # ======================================================
    # Registration
    # ======================================================

    def add_thumbnail(
        self,
        key: str,
        path: str | Path,
    ) -> None:
        self.thumbnails[key] = CacheEntry(
            path=Path(path),
        )

    def add_waveform(
        self,
        key: str,
        path: str | Path,
    ) -> None:
        self.waveforms[key] = CacheEntry(
            path=Path(path),
        )

    def add_proxy(
        self,
        key: str,
        path: str | Path,
    ) -> None:
        self.proxies[key] = CacheEntry(
            path=Path(path),
        )

    def add_preview_frame(
        self,
        frame: int,
        path: str | Path,
    ) -> None:
        self.preview_frames[frame] = CacheEntry(
            path=Path(path),
        )

    # ======================================================
    # Lookup
    # ======================================================

    def get_thumbnail(
        self,
        key: str,
    ) -> CacheEntry | None:
        return self.thumbnails.get(key)

    def get_proxy(
        self,
        key: str,
    ) -> CacheEntry | None:
        return self.proxies.get(key)

    def get_waveform(
        self,
        key: str,
    ) -> CacheEntry | None:
        return self.waveforms.get(key)

    # ======================================================
    # Removal
    # ======================================================

    def invalidate_asset(
        self,
        asset_id: str,
    ) -> None:
        """
        Remove every cache associated with an asset.
        """

        self.thumbnails.pop(asset_id, None)
        self.waveforms.pop(asset_id, None)
        self.proxies.pop(asset_id, None)
        self.audio_cache.pop(asset_id, None)
        self.preview_videos.pop(asset_id, None)

    def clear_preview(self) -> None:
        self.preview_frames.clear()
        self.rendered_frames.clear()
        self.preview_videos.clear()
        self.preview_audio.clear()

    def clear_proxies(self) -> None:
        self.proxies.clear()

    def clear_gpu(self) -> None:
        self.gpu.clear()

    def clear(self) -> None:
        self.thumbnails.clear()
        self.preview_frames.clear()
        self.rendered_frames.clear()
        self.waveforms.clear()
        self.audio_cache.clear()
        self.proxies.clear()
        self.preview_videos.clear()
        self.preview_audio.clear()
        self.subtitles.clear()
        self.overlays.clear()
        self.filters.clear()
        self.gpu.clear()
        self.metadata.clear()

    # ======================================================
    # Statistics
    # ======================================================

    @computed_field
    @property
    def thumbnail_count(self) -> int:
        return len(self.thumbnails)

    @computed_field
    @property
    def waveform_count(self) -> int:
        return len(self.waveforms)

    @computed_field
    @property
    def proxy_count(self) -> int:
        return len(self.proxies)

    @computed_field
    @property
    def preview_frame_count(self) -> int:
        return len(self.preview_frames)

    @computed_field
    @property
    def preview_video_count(self) -> int:
        return len(self.preview_videos)

    @computed_field
    @property
    def total_size_bytes(self) -> int:
        groups = (
            self.thumbnails,
            self.preview_frames,
            self.rendered_frames,
            self.waveforms,
            self.audio_cache,
            self.proxies,
            self.preview_videos,
            self.preview_audio,
            self.subtitles,
            self.overlays,
        )

        total = 0

        for group in groups:
            total += sum(entry.size_bytes for entry in group.values())

        return total

    @computed_field
    @property
    def total_size_mb(self) -> float:
        return round(
            self.total_size_bytes / (1024 * 1024),
            2,
        )

    @computed_field
    @property
    def is_empty(self) -> bool:
        return (
            self.thumbnail_count == 0
            and self.waveform_count == 0
            and self.proxy_count == 0
            and self.preview_frame_count == 0
            and self.preview_video_count == 0
            and not self.filters
            and not self.gpu
        )

    # ======================================================
    # Representation
    # ======================================================

    def __repr__(self) -> str:
        return (
            "RenderCache("
            f"thumbnails={self.thumbnail_count}, "
            f"waveforms={self.waveform_count}, "
            f"proxies={self.proxy_count}, "
            f"preview_frames={self.preview_frame_count}, "
            f"size={self.total_size_mb:.2f} MB)"
        )
