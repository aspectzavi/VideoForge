"""
VideoForge Asset Reference

References a MediaAsset without owning it.

AssetReference is used throughout the editor wherever an object needs
to point to an asset while allowing per-reference metadata.

Examples
--------
Timeline Clip
Composition
Overlay
Media Bin
Collection
Favorites
Search Results
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, computed_field


class AssetReference(BaseModel):
    """
    Reference to a MediaAsset.
    """

    model_config = ConfigDict(
        arbitrary_types_allowed=True,
    )

    # ------------------------------------------------------------------
    # Timestamps
    # ------------------------------------------------------------------

    created_at: datetime = Field(default_factory=datetime.utcnow)
    modified_at: datetime = Field(default_factory=datetime.utcnow)

    # ------------------------------------------------------------------
    # Identity
    # ------------------------------------------------------------------

    id: str = Field(default_factory=lambda: uuid.uuid4().hex)

    # ID of the MediaAsset this reference points to
    asset_id: str

    # ------------------------------------------------------------------
    # Optional user metadata
    # ------------------------------------------------------------------

    name: str | None = None
    label: str | None = None
    notes: str | None = None

    favorite: bool = False
    enabled: bool = True
    offline: bool = False

    proxy_asset_id: str | None = None
    usage_count: int = 0

    rating: int = Field(default=0, ge=0, le=5)

    tags: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    # ==================================================================
    # Computed Properties
    # ==================================================================

    @computed_field
    @property
    def has_notes(self) -> bool:
        return bool(self.notes)

    @computed_field
    @property
    def is_rated(self) -> bool:
        return self.rating > 0

    @computed_field
    @property
    def is_disabled(self) -> bool:
        return not self.enabled

    @computed_field
    @property
    def is_offline(self) -> bool:
        return self.offline

    @computed_field
    @property
    def reference_key(self) -> str:
        return f"{self.asset_id}:{self.id}"

    # ==================================================================
    # Tags
    # ==================================================================

    def add_tag(self, tag: str) -> None:
        if tag not in self.tags:
            self.tags.append(tag)
            self.touch()

    def remove_tag(self, tag: str) -> bool:
        if tag not in self.tags:
            return False
        self.tags.remove(tag)
        self.touch()
        return True

    def clear_tags(self) -> None:
        self.tags.clear()
        self.touch()

    def has_tag(self, tag: str) -> bool:
        return tag in self.tags

    # ==================================================================
    # Rating
    # ==================================================================

    def set_rating(self, rating: int) -> None:
        self.rating = max(0, min(5, rating))
        self.touch()

    def clear_rating(self) -> None:
        self.rating = 0
        self.touch()

    # ==================================================================
    # State
    # ==================================================================

    def enable(self) -> None:
        self.enabled = True
        self.touch()

    def disable(self) -> None:
        self.enabled = False
        self.touch()

    def toggle(self) -> None:
        self.enabled = not self.enabled
        self.touch()

    def mark_favorite(self) -> None:
        self.favorite = True
        self.touch()

    def unmark_favorite(self) -> None:
        self.favorite = False
        self.touch()

    def toggle_favorite(self) -> None:
        self.favorite = not self.favorite
        self.touch()

    def mark_offline(self) -> None:
        self.offline = True
        self.touch()

    def mark_online(self) -> None:
        self.offline = False
        self.touch()

    # ==================================================================
    # Metadata
    # ==================================================================

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

    # ==================================================================
    # Utilities
    # ==================================================================

    def rename(self, name: str | None) -> None:
        self.name = name
        self.touch()

    def set_label(self, label: str | None) -> None:
        self.label = label
        self.touch()

    def set_notes(self, notes: str | None) -> None:
        self.notes = notes
        self.touch()

    def increment_usage(self) -> None:
        self.usage_count += 1
        self.touch()

    def reset_usage(self) -> None:
        self.usage_count = 0
        self.touch()

    def touch(self) -> None:
        """Update the modified_at timestamp."""
        self.modified_at = datetime.utcnow()

    def clone(self) -> AssetReference:
        """Deep-copy the reference and assign a new unique ID."""
        clone = self.model_copy(deep=True)
        clone.id = uuid.uuid4().hex
        clone.created_at = datetime.utcnow()
        clone.modified_at = datetime.utcnow()
        return clone

    # ==================================================================
    # Representation
    # ==================================================================

    def __str__(self) -> str:
        return self.name or self.asset_id

    def __repr__(self) -> str:
        return (
            "AssetReference("
            f"asset_id='{self.asset_id}', "
            f"favorite={self.favorite}, "
            f"enabled={self.enabled})"
        )
