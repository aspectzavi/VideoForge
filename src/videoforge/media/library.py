"""
VideoForge Media Library

The Media Library owns every imported MediaAsset for a project.

Unlike the Timeline, which contains Clips, the Library stores the
original source assets and organizes them into bins and collections.

Responsibilities
----------------
- Import media
- Remove media
- Search assets
- Organize bins
- Organize collections
- Create asset references
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, computed_field

from videoforge.media.asset import MediaAsset
from videoforge.media.asset_reference import AssetReference
from videoforge.media.bin import MediaBin
from videoforge.media.collection import MediaCollection


class MediaLibrary(BaseModel):
    """
    Central asset manager.
    """

    model_config = ConfigDict(
        arbitrary_types_allowed=True,
    )

    # ==========================================================
    # Assets
    # ==========================================================

    assets: list[MediaAsset] = Field(
        default_factory=list,
    )

    # ==========================================================
    # Organization
    # ==========================================================

    bins: list[MediaBin] = Field(
        default_factory=list,
    )

    collections: list[MediaCollection] = Field(
        default_factory=list,
    )

    # ==========================================================
    # Metadata
    # ==========================================================

    metadata: dict[str, Any] = Field(
        default_factory=dict,
    )

    # ==========================================================
    # Import
    # ==========================================================

    def import_file(
        self,
        path: str | Path,
    ) -> MediaAsset:

        path = Path(path).resolve()

        asset = self.find(path)

        if asset is not None:
            return asset

        asset = MediaAsset.load(path)

        self.assets.append(asset)

        return asset

    def import_files(
        self,
        paths: list[str | Path],
    ) -> list[MediaAsset]:

        return [self.import_file(path) for path in paths]

    # ==========================================================
    # Removal
    # ==========================================================

    def remove(
        self,
        asset: MediaAsset,
    ) -> None:

        if asset in self.assets:
            self.assets.remove(asset)

    def remove_path(
        self,
        path: str | Path,
    ) -> bool:

        asset = self.find(path)

        if asset is None:
            return False

        self.remove(asset)

        return True

    # ==========================================================
    # Lookup
    # ==========================================================

    def find(
        self,
        path: str | Path,
    ) -> MediaAsset | None:

        path = Path(path).resolve()

        for asset in self.assets:
            if asset.path.resolve() == path:
                return asset

        return None

    def find_by_name(
        self,
        filename: str,
    ) -> MediaAsset | None:

        filename = filename.lower()

        for asset in self.assets:
            if asset.filename.lower() == filename:
                return asset

        return None

    def find_by_id(
        self,
        asset_id: str,
    ) -> MediaAsset | None:

        for asset in self.assets:
            if asset.id == asset_id:
                return asset

        return None

    def contains(
        self,
        path: str | Path,
    ) -> bool:

        return self.find(path) is not None

    # ==========================================================
    # References
    # ==========================================================

    def reference(
        self,
        asset: MediaAsset,
    ) -> AssetReference:

        return AssetReference(
            asset_id=asset.id,
            name=asset.filename,
        )

    def resolve(
        self,
        reference: AssetReference,
    ) -> MediaAsset | None:

        return self.find_by_id(
            reference.asset_id,
        )

    # ==========================================================
    # Organization
    # ==========================================================

    def create_bin(
        self,
        name: str,
    ) -> MediaBin:

        bin_ = MediaBin(name=name)

        self.bins.append(bin_)

        return bin_

    def create_collection(
        self,
        name: str,
    ) -> MediaCollection:

        collection = MediaCollection(
            name=name,
        )

        self.collections.append(
            collection,
        )

        return collection

    # ==========================================================
    # Filtering
    # ==========================================================

    def videos(self) -> list[MediaAsset]:

        return [asset for asset in self.assets if asset.asset_type == "video"]

    def audios(self) -> list[MediaAsset]:

        return [asset for asset in self.assets if asset.asset_type == "audio"]

    def images(self) -> list[MediaAsset]:

        return [asset for asset in self.assets if asset.asset_type == "image"]

    def gifs(self) -> list[MediaAsset]:

        return [asset for asset in self.assets if asset.asset_type == "gif"]

    def search(
        self,
        text: str,
    ) -> list[MediaAsset]:

        text = text.lower()

        return [asset for asset in self.assets if text in asset.filename.lower()]

    # ==========================================================
    # Sorting
    # ==========================================================

    def sort_by_name(self) -> None:

        self.assets.sort(
            key=lambda a: a.filename.lower(),
        )

    def sort_by_size(self) -> None:

        self.assets.sort(
            key=lambda a: a.size_bytes,
        )

    def sort_by_duration(self) -> None:

        self.assets.sort(
            key=lambda a: a.duration,
        )

    # ==========================================================
    # Statistics
    # ==========================================================

    @computed_field
    @property
    def asset_count(self) -> int:
        return len(self.assets)

    @computed_field
    @property
    def bin_count(self) -> int:
        return len(self.bins)

    @computed_field
    @property
    def collection_count(self) -> int:
        return len(self.collections)

    @computed_field
    @property
    def total_size_bytes(self) -> int:
        return sum(asset.size_bytes for asset in self.assets)

    @computed_field
    @property
    def total_size_mb(self) -> float:
        return round(
            self.total_size_bytes / (1024 * 1024),
            2,
        )

    @computed_field
    @property
    def video_count(self) -> int:
        return len(self.videos())

    @computed_field
    @property
    def audio_count(self) -> int:
        return len(self.audios())

    @computed_field
    @property
    def image_count(self) -> int:
        return len(self.images())

    @computed_field
    @property
    def is_empty(self) -> bool:
        return not self.assets

    # ==========================================================
    # Utilities
    # ==========================================================

    def clear(self) -> None:

        self.assets.clear()
        self.bins.clear()
        self.collections.clear()

    def summary(self) -> dict[str, Any]:

        return {
            "assets": self.asset_count,
            "videos": self.video_count,
            "audio": self.audio_count,
            "images": self.image_count,
            "bins": self.bin_count,
            "collections": self.collection_count,
            "size_mb": self.total_size_mb,
        }

    def __len__(self) -> int:
        return len(self.assets)

    def __getitem__(
        self,
        index: int,
    ) -> MediaAsset:
        return self.assets[index]

    def __repr__(self) -> str:

        return (
            "MediaLibrary("
            f"assets={self.asset_count}, "
            f"bins={self.bin_count}, "
            f"collections={self.collection_count}, "
            f"videos={self.video_count}, "
            f"audio={self.audio_count}, "
            f"images={self.image_count}, "
            f"size={self.total_size_mb:.2f} MB)"
        )
