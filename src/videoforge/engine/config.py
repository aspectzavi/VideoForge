"""
VideoForge Configuration Manager

Handles loading, saving, and merging project configuration files.

Supports:
- YAML configuration
- Default values
- Project overrides
- Configuration profiles
- Runtime updates

Example
-------

from videoforge.engine.config import config

print(config.project.output_directory)
print(config.render.video_codec)
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field

from videoforge.engine.constants import CONFIG_DIR
from videoforge.engine.settings import settings

# ==========================================================
# Config Sections
# ==========================================================


class ProjectConfig(BaseModel):
    name: str = "VideoForge Project"

    output_directory: Path = settings.output_dir

    temp_directory: Path = settings.temp_dir

    cache_directory: Path = settings.cache_dir

    overwrite: bool = True


class RenderConfig(BaseModel):
    video_codec: str = settings.default_video_codec

    audio_codec: str = settings.default_audio_codec

    preset: str = settings.default_preset

    crf: int = settings.default_crf

    fps: int = settings.default_fps

    pixel_format: str = settings.default_pixel_format

    faststart: bool = settings.faststart


class VerticalConfig(BaseModel):
    enabled: bool = True

    mode: str = settings.vertical_mode

    width: int = settings.vertical_width

    height: int = settings.vertical_height


class CaptionConfig(BaseModel):
    enabled: bool = True

    font: str = settings.caption_font

    font_size: int = settings.caption_font_size

    stroke_width: int = settings.caption_stroke_width

    max_words: int = settings.caption_max_words

    bottom_margin: int = settings.caption_bottom_margin


class AIConfig(BaseModel):
    enabled: bool = settings.ai_enabled

    whisper_model: str = settings.whisper_model

    compute_type: str = settings.whisper_compute_type

    batch_size: int = settings.whisper_batch_size

    mediapipe: bool = settings.mediapipe_enabled

    llm: bool = settings.llm_enabled


class LoggingConfig(BaseModel):
    level: str = settings.log_level

    debug: bool = settings.debug

    log_directory: Path = settings.logs_dir


class PluginConfig(BaseModel):
    enabled: bool = settings.plugins_enabled

    directory: Path = settings.plugin_directory


# ==========================================================
# Root Configuration
# ==========================================================


class VideoForgeConfig(BaseModel):
    project: ProjectConfig = Field(default_factory=ProjectConfig)

    render: RenderConfig = Field(default_factory=RenderConfig)

    vertical: VerticalConfig = Field(default_factory=VerticalConfig)

    captions: CaptionConfig = Field(default_factory=CaptionConfig)

    ai: AIConfig = Field(default_factory=AIConfig)

    logging: LoggingConfig = Field(default_factory=LoggingConfig)

    plugins: PluginConfig = Field(default_factory=PluginConfig)


# ==========================================================
# Manager
# ==========================================================


class ConfigManager:
    """
    Loads and saves VideoForge configuration.
    """

    def __init__(
        self,
        path: str | Path | None = None,
    ) -> None:

        self.path = Path(path) if path else (CONFIG_DIR / "videoforge.yaml")

        self.config = VideoForgeConfig()

        if self.path.exists():
            self.load()

    # ------------------------------------------------------

    def load(self) -> VideoForgeConfig:
        """
        Load configuration from YAML.
        """

        with self.path.open(
            "r",
            encoding="utf-8",
        ) as f:
            data = yaml.safe_load(f) or {}

        self.config = VideoForgeConfig.model_validate(data)

        return self.config

    # ------------------------------------------------------

    def save(self) -> None:
        """
        Save configuration to YAML.
        """

        self.path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        with self.path.open(
            "w",
            encoding="utf-8",
        ) as f:
            yaml.safe_dump(
                self.config.model_dump(mode="python"),
                f,
                sort_keys=False,
                allow_unicode=True,
            )

    # ------------------------------------------------------

    def reset(self) -> None:
        """
        Reset to defaults.
        """

        self.config = VideoForgeConfig()

    # ------------------------------------------------------

    def update(
        self,
        **kwargs: Any,
    ) -> None:
        """
        Update root-level configuration values.

        Example
        -------
        config.update(
            render={
                "crf":18
            }
        )
        """

        current = self.config.model_dump()

        current.update(kwargs)

        self.config = VideoForgeConfig.model_validate(current)

    # ------------------------------------------------------

    def profile(
        self,
        name: str,
    ) -> None:
        """
        Apply a built-in configuration profile.
        """

        name = name.lower()

        if name == "tiktok":
            self.config.vertical.mode = "blur"
            self.config.render.crf = 20
            self.config.render.fps = 30

        elif name == "shorts":
            self.config.vertical.mode = "crop"
            self.config.render.crf = 18
            self.config.render.fps = 60

        elif name == "reels":
            self.config.vertical.mode = "fit"
            self.config.render.crf = 20
            self.config.render.fps = 30

        else:
            raise ValueError(f"Unknown profile '{name}'")

    # ------------------------------------------------------

    def get(
        self,
        dotted_key: str,
        default: Any = None,
    ) -> Any:
        """
        Get a value using dot notation.

        Example
        -------
        config.get("render.crf")
        """

        value: Any = self.config

        for part in dotted_key.split("."):
            if hasattr(value, part):
                value = getattr(value, part)

            else:
                return default

        return value

    # ------------------------------------------------------

    def set(
        self,
        dotted_key: str,
        value: Any,
    ) -> None:
        """
        Set a value using dot notation.

        Example
        -------
        config.set("render.crf", 18)
        """

        parts = dotted_key.split(".")

        obj: Any = self.config

        for part in parts[:-1]:
            obj = getattr(obj, part)

        setattr(
            obj,
            parts[-1],
            value,
        )

    # ------------------------------------------------------

    def as_dict(self) -> dict[str, Any]:
        """
        Return the configuration as a dictionary.
        """

        return self.config.model_dump()

    # ------------------------------------------------------

    def __getitem__(
        self,
        key: str,
    ) -> Any:

        return self.get(key)

    # ------------------------------------------------------

    def __setitem__(
        self,
        key: str,
        value: Any,
    ) -> None:

        self.set(
            key,
            value,
        )


# ==========================================================
# Singleton
# ==========================================================


config = ConfigManager()
