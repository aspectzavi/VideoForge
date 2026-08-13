"""
VideoForge Media Collection

Collections are logical groupings of assets.

Unlike MediaBins, collections do not represent folders. An asset may belong
to any number of collections.

Collections may be:

- Manual
- Smart (rule-based)
- Temporary
"""

from __future__ import annotations

import uuid
from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, computed_field


class CollectionType(StrEnum):
    MANUAL = "manual"
    SMART = "smart"
    TEMPORARY = "temporary"


class CollectionRule(BaseModel):
    """
    Rule used by a smart collection.

    Examples
    --------
    asset_type == "video"
    duration > 60
    tag contains "drone"
    """

    field: str
    operator: str
    value: Any
    case_sensitive: bool = False
    visible: bool = True
    last_evaluated: datetime | None = None
    sort_mode: str = "name"


class MediaCollection(BaseModel):
    """
    Logical grouping of assets.

    Assets are referenced by ID rather than embedded.
    """

    model_config = ConfigDict(
        arbitrary_types_allowed=True,
    )

    # -------------------------------------------------------------
    # Timestamps
    # -------------------------------------------------------------

    created_at: datetime = Field(default_factory=datetime.utcnow)
    modified_at: datetime = Field(default_factory=datetime.utcnow)

    # -------------------------------------------------------------
    # Identity
    # -------------------------------------------------------------

    id: str = Field(default_factory=lambda: uuid.uuid4().hex)
    name: str
    description: str | None = None
    color: str | None = None

    # -------------------------------------------------------------
    # Type
    # -------------------------------------------------------------

    type: CollectionType = CollectionType.MANUAL

    # -------------------------------------------------------------
    # Assets
    # -------------------------------------------------------------

    asset_ids: list[str] = Field(default_factory=list)

    # -------------------------------------------------------------
    # Smart Collection Rules
    # -------------------------------------------------------------

    rules: list[CollectionRule] = Field(default_factory=list)

    # -------------------------------------------------------------
    # Metadata
    # -------------------------------------------------------------

    tags: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    # =============================================================
    # Computed Properties
    # =============================================================

    @computed_field
    @property
    def asset_count(self) -> int:
        return len(self.asset_ids)

    @computed_field
    @property
    def is_empty(self) -> bool:
        return self.asset_count == 0

    @computed_field
    @property
    def is_manual(self) -> bool:
        return self.type == CollectionType.MANUAL

    @computed_field
    @property
    def is_smart(self) -> bool:
        return self.type == CollectionType.SMART

    @computed_field
    @property
    def is_temporary(self) -> bool:
        return self.type == CollectionType.TEMPORARY

    # =============================================================
    # Assets
    # =============================================================

    def add_asset(self, asset_id: str) -> None:
        """Add a single asset ID if it is not already present."""
        if asset_id not in self.asset_ids:
            self.asset_ids.append(asset_id)
            self.touch()

    def add_assets(self, asset_ids: list[str]) -> None:
        """Add multiple asset IDs, skipping duplicates."""
        for asset_id in asset_ids:
            self.add_asset(asset_id)

    def remove_asset(self, asset_id: str) -> bool:
        """Remove an asset ID. Returns True if it was present and removed."""
        if asset_id not in self.asset_ids:
            return False
        self.asset_ids.remove(asset_id)
        self.touch()
        return True

    def contains(self, asset_id: str) -> bool:
        """Return True if the collection contains the given asset ID."""
        return asset_id in self.asset_ids

    def clear_assets(self) -> None:
        """Remove all asset IDs from the collection."""
        self.asset_ids.clear()
        self.touch()

    # =============================================================
    # Rules (Smart Collections)
    # =============================================================

    def add_rule(self, rule: CollectionRule) -> None:
        """Append a rule to the smart collection."""
        self.rules.append(rule)
        self.touch()

    def remove_rule(self, rule: CollectionRule) -> bool:
        """Remove a specific rule. Returns True if it was present."""
        if rule in self.rules:
            self.rules.remove(rule)
            self.touch()
            return True
        return False

    def clear_rules(self) -> None:
        """Remove all rules."""
        self.rules.clear()
        self.touch()

    # =============================================================
    # Tags
    # =============================================================

    def add_tag(self, tag: str) -> None:
        if tag not in self.tags:
            self.tags.append(tag)
            self.touch()

    def remove_tag(self, tag: str) -> bool:
        if tag in self.tags:
            self.tags.remove(tag)
            self.touch()
            return True
        return False

    def clear_tags(self) -> None:
        self.tags.clear()
        self.touch()

    # =============================================================
    # Utilities
    # =============================================================

    def rename(self, name: str) -> None:
        """Rename the collection and update modified_at."""
        self.name = name
        self.touch()

    def set_color(self, color: str | None) -> None:
        self.color = color
        self.touch()

    def set_description(self, description: str | None) -> None:
        self.description = description
        self.touch()

    def touch(self) -> None:
        """Update the modified_at timestamp."""
        self.modified_at = datetime.utcnow()

    def clear(self) -> None:
        """Clear both assets and rules."""
        self.asset_ids.clear()
        self.rules.clear()
        self.touch()

    def clone(self) -> MediaCollection:
        """Deep-copy the collection and assign a new unique ID."""
        clone = self.model_copy(deep=True)
        clone.id = uuid.uuid4().hex
        clone.created_at = datetime.utcnow()
        clone.modified_at = datetime.utcnow()
        return clone

    # =============================================================
    # Representation
    # =============================================================

    def __str__(self) -> str:
        return self.name

    def __repr__(self) -> str:
        return (
            "MediaCollection("
            f"name='{self.name}', "
            f"type='{self.type.value}', "
            f"assets={self.asset_count})"
        )

    def __len__(self) -> int:
        return len(self.asset_ids)

    def __contains__(self, asset_id: str) -> bool:
        return asset_id in self.asset_ids
