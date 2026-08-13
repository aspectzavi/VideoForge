"""
VideoForge Media Proxy

Represents a proxy version of an original media asset.

A proxy is a lower-resolution or lower-bitrate copy used for editing.
During final rendering, VideoForge automatically switches back to the
original media.

Example
-------
Original
    4K HEVC 120 Mbps

Proxy
    720p H.264 5 Mbps
"""

from __future__ import annotations

import uuid
from datetime import datetime
from enum import StrEnum
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, computed_field


class ProxyStatus(StrEnum):
    PENDING = "pending"
    GENERATING = "generating"
    READY = "ready"
    MISSING = "missing"
    FAILED = "failed"


class MediaProxy(BaseModel):
    """
    Proxy media associated with an asset.
    """

    model_config = ConfigDict(
        arbitrary_types_allowed=True,
    )

    # ------------------------------------------------------------------
    # Timestamps
    # ------------------------------------------------------------------

    created_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: datetime | None = None
    modified_at: datetime = Field(default_factory=datetime.utcnow)

    # ------------------------------------------------------------------
    # Identity
    # ------------------------------------------------------------------

    id: str = Field(default_factory=lambda: uuid.uuid4().hex)
    asset_id: str

    # ------------------------------------------------------------------
    # Files
    # ------------------------------------------------------------------

    original_path: Path
    proxy_path: Path

    # ------------------------------------------------------------------
    # Generation parameters
    # ------------------------------------------------------------------

    width: int | None = Field(default=None, gt=0)
    height: int | None = Field(default=None, gt=0)
    bitrate: int | None = Field(default=None, gt=0)
    codec: str | None = None
    preset: str | None = None

    status: ProxyStatus = ProxyStatus.PENDING

    # ------------------------------------------------------------------
    # Metadata
    # ------------------------------------------------------------------

    metadata: dict[str, Any] = Field(default_factory=dict)

    # ==================================================================
    # Computed Properties
    # ==================================================================

    @computed_field
    @property
    def exists(self) -> bool:
        return self.proxy_path.exists()

    @computed_field
    @property
    def size_bytes(self) -> int:
        if not self.exists:
            return 0
        return self.proxy_path.stat().st_size

    @computed_field
    @property
    def size_mb(self) -> float:
        return round(self.size_bytes / (1024 * 1024), 2)

    @computed_field
    @property
    def resolution(self) -> str | None:
        if self.width is None or self.height is None:
            return None
        return f"{self.width}x{self.height}"

    @computed_field
    @property
    def is_ready(self) -> bool:
        return self.status == ProxyStatus.READY and self.exists

    @computed_field
    @property
    def is_missing(self) -> bool:
        return not self.exists or self.status == ProxyStatus.MISSING

    @computed_field
    @property
    def is_failed(self) -> bool:
        return self.status == ProxyStatus.FAILED

    @computed_field
    @property
    def is_generating(self) -> bool:
        return self.status == ProxyStatus.GENERATING

    @computed_field
    @property
    def is_pending(self) -> bool:
        return self.status == ProxyStatus.PENDING

    @computed_field
    @property
    def original_exists(self) -> bool:
        return self.original_path.exists()

    @computed_field
    @property
    def active_path(self) -> Path:
        """Return the path that should be used for playback/editing."""
        if self.is_ready:
            return self.proxy_path
        return self.original_path

    # ==================================================================
    # State Management
    # ==================================================================

    def mark_pending(self) -> None:
        self.status = ProxyStatus.PENDING
        self.touch()

    def mark_generating(self) -> None:
        self.status = ProxyStatus.GENERATING
        self.touch()

    def mark_ready(self) -> None:
        self.status = ProxyStatus.READY
        self.completed_at = datetime.utcnow()
        self.touch()

    def mark_failed(self) -> None:
        self.status = ProxyStatus.FAILED
        self.touch()

    def mark_missing(self) -> None:
        self.status = ProxyStatus.MISSING
        self.touch()

    def relink(self, path: Path) -> None:
        """Point the proxy to a new file path and refresh status."""
        self.proxy_path = path
        self.refresh()
        self.touch()

    # ==================================================================
    # Utilities
    # ==================================================================

    def refresh(self) -> None:
        """
        Synchronize status with the filesystem.
        """
        if self.proxy_path.exists():
            if self.status in (ProxyStatus.MISSING, ProxyStatus.PENDING):
                self.status = ProxyStatus.READY
                if self.completed_at is None:
                    self.completed_at = datetime.utcnow()
        else:
            if self.status == ProxyStatus.READY:
                self.status = ProxyStatus.MISSING
        self.touch()

    def delete(self) -> None:
        """
        Delete the proxy file if it exists and mark as missing.
        """
        if self.proxy_path.exists():
            self.proxy_path.unlink()
        self.status = ProxyStatus.MISSING
        self.completed_at = None
        self.touch()

    def set_metadata(self, key: str, value: Any) -> None:
        self.metadata[key] = value
        self.touch()

    def get_metadata(self, key: str, default: Any = None) -> Any:
        return self.metadata.get(key, default)

    def remove_metadata(self, key: str) -> None:
        self.metadata.pop(key, None)
        self.touch()

    def clear_metadata(self) -> None:
        self.metadata.clear()
        self.touch()

    def touch(self) -> None:
        """Update the modified_at timestamp."""
        self.modified_at = datetime.utcnow()

    def clone(self) -> MediaProxy:
        """Deep-copy the proxy and assign a new unique ID."""
        clone = self.model_copy(deep=True)
        clone.id = uuid.uuid4().hex
        clone.created_at = datetime.utcnow()
        clone.modified_at = datetime.utcnow()
        return clone

    # ==================================================================
    # Representation
    # ==================================================================

    def __str__(self) -> str:
        return str(self.proxy_path)

    def __repr__(self) -> str:
        return (
            "MediaProxy("
            f"status='{self.status.value}', "
            f"resolution='{self.resolution}', "
            f"path='{self.proxy_path.name}')"
        )
