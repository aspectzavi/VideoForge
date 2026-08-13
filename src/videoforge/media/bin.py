"""
VideoForge Media Bin

A Bin is a virtual folder used to organize media assets inside a project.

Unlike operating system folders, bins do not own media files. They simply
reference assets already stored in the MediaLibrary.

Examples
--------
Project
├── Media Library
│   ├── intro.mp4
│   ├── logo.png
│   └── music.mp3
│
├── Bins
│   ├── Footage
│   ├── Music
│   ├── Logos
│   └── Archive
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, computed_field


class MediaBin(BaseModel):
    """
    Organizes assets by their IDs.

    The actual Asset objects remain inside MediaLibrary.
    """

    model_config = ConfigDict(
        arbitrary_types_allowed=True,
    )

    # ------------------------------------------------------------------
    # Identity
    # ------------------------------------------------------------------

    id: str = Field(
        default_factory=lambda: uuid.uuid4().hex,
    )

    name: str

    bin_type: str = "folder"

    sort_mode: str = "name"

    color: str | None = None

    description: str | None = None

    # ------------------------------------------------------------------
    # Hierarchy
    # ------------------------------------------------------------------

    parent_id: str | None = None

    child_bins: list[str] = Field(
        default_factory=list,
    )

    # ------------------------------------------------------------------
    # Asset References
    # ------------------------------------------------------------------

    asset_ids: list[str] = Field(
        default_factory=list,
    )

    # ------------------------------------------------------------------
    # Metadata
    # ------------------------------------------------------------------

    tags: list[str] = Field(
        default_factory=list,
    )

    metadata: dict[str, Any] = Field(
        default_factory=dict,
    )

    created_at: datetime = Field(
        default_factory=datetime.utcnow,
    )

    modified_at: datetime = Field(
        default_factory=datetime.utcnow,
    )

    # ==================================================================
    # Computed
    # ==================================================================

    @computed_field
    @property
    def asset_count(self) -> int:
        return len(self.asset_ids)

    @computed_field
    @property
    def child_count(self) -> int:
        return len(self.child_bins)

    @computed_field
    @property
    def is_root(self) -> bool:
        return self.parent_id is None

    @computed_field
    @property
    def is_empty(self) -> bool:
        return self.asset_count == 0

    # ==================================================================
    # Assets
    # ==================================================================

    def add_asset(self, asset_id: str) -> None:
        if asset_id not in self.asset_ids:
            self.asset_ids.append(asset_id)

    def add_assets(self, asset_ids: list[str]) -> None:
        for asset_id in asset_ids:
            self.add_asset(asset_id)

    def remove_asset(self, asset_id: str) -> bool:
        if asset_id not in self.asset_ids:
            return False

        self.asset_ids.remove(asset_id)
        return True

    def contains(self, asset_id: str) -> bool:
        return asset_id in self.asset_ids

    def clear_assets(self) -> None:
        self.asset_ids.clear()

    # ==================================================================
    # Child Bins
    # ==================================================================

    def add_child(self, bin_id: str) -> None:
        if bin_id not in self.child_bins:
            self.child_bins.append(bin_id)

    def remove_child(self, bin_id: str) -> bool:
        if bin_id not in self.child_bins:
            return False

        self.child_bins.remove(bin_id)
        return True

    # ==================================================================
    # Utilities
    # ==================================================================

    def rename(self, name: str) -> None:
        self.name = name
        self.touch()

    def clone(self) -> MediaBin:
        clone = self.model_copy(deep=True)
        clone.id = uuid.uuid4().hex
        return clone

    def touch(self) -> None:
        self.modified_at = datetime.utcnow()

    def all_bin_ids(self) -> list[str]:

        return [
            self.id,
            *self.child_bins,
        ]

    def sort_assets(self) -> None:

        self.asset_ids.sort()

    # ==================================================================
    # Representation
    # ==================================================================

    def __str__(self) -> str:
        return self.name

    def __repr__(self) -> str:
        return f"MediaBin(name='{self.name}', assets={self.asset_count}, children={self.child_count})"
