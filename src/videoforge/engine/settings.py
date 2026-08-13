"""
VideoForge Settings

Central application settings.

Features
--------
- Environment variable support (.env)
- Strongly typed settings via Pydantic
- Automatic directory creation
- FFmpeg configuration
- AI model configuration
- Export defaults
- Logging configuration
- Hardware configuration

Usage
-----

from videoforge.engine.settings import settings

print(settings.output_dir)
print(settings.ffmpeg_path)
"""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from videoforge.engine.constants import (
    CACHE_DIR,
    CONFIG_DIR,
    DEFAULT_ENV_FILE,
    LOGS_DIR,
    OUTPUT_DIR,
    TEMP_DIR,
)


class Settings(BaseSettings):
    """
    Global VideoForge settings.
    """

    model_config = SettingsConfigDict(
        env_file=DEFAULT_ENV_FILE,
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ==========================================================
    # General
    # ==========================================================

    app_name: str = "VideoForge"

    debug: bool = False

    log_level: str = "INFO"

    timezone: str = "UTC"

    # ==========================================================
    # Paths
    # ==========================================================

    output_dir: Path = OUTPUT_DIR

    cache_dir: Path = CACHE_DIR

    temp_dir: Path = TEMP_DIR

    logs_dir: Path = LOGS_DIR

    config_dir: Path = CONFIG_DIR

    # ==========================================================
    # FFmpeg
    # ==========================================================

    ffmpeg_path: str = "ffmpeg"

    ffprobe_path: str = "ffprobe"

    ffplay_path: str = "ffplay"

    ffmpeg_threads: int = max(
        1,
        os.cpu_count() or 4,
    )

    ffmpeg_log_level: str = "error"

    overwrite_output: bool = True

    # ==========================================================
    # Rendering
    # ==========================================================

    default_video_codec: str = "libx264"

    default_audio_codec: str = "aac"

    default_audio_bitrate: str = "192k"

    default_preset: str = "medium"

    default_crf: int = 20

    default_pixel_format: str = "yuv420p"

    default_fps: int = 30

    default_sample_rate: int = 48000

    # ==========================================================
    # AI
    # ==========================================================

    ai_enabled: bool = True

    ai_device: str = "auto"

    whisper_model: str = "base"

    whisper_compute_type: str = "float16"

    whisper_batch_size: int = 16

    whisper_threads: int = max(
        1,
        (os.cpu_count() or 4) // 2,
    )

    mediapipe_enabled: bool = True

    llm_enabled: bool = False

    # ==========================================================
    # Caption Defaults
    # ==========================================================

    caption_font: str = "Arial"

    caption_font_size: int = 56

    caption_stroke_width: int = 3

    caption_max_words: int = 4

    caption_bottom_margin: int = 120

    # ==========================================================
    # Vertical Video
    # ==========================================================

    vertical_width: int = 1080

    vertical_height: int = 1920

    vertical_mode: str = "blur"

    # ==========================================================
    # Export
    # ==========================================================

    faststart: bool = True

    export_thumbnail: bool = False

    keep_temp_files: bool = False

    # ==========================================================
    # Plugins
    # ==========================================================

    plugins_enabled: bool = True

    plugin_directory: Path = Field(
        default_factory=lambda: Path("plugins"),
    )

    # ==========================================================
    # Hardware
    # ==========================================================

    use_gpu: bool = True

    gpu_encoder: str = "auto"

    gpu_decoder: str = "auto"

    # ==========================================================
    # Validation
    # ==========================================================

    @field_validator(
        "log_level",
        mode="before",
    )
    @classmethod
    def validate_log_level(
        cls,
        value: str,
    ) -> str:

        value = value.upper()

        allowed = {
            "TRACE",
            "DEBUG",
            "INFO",
            "SUCCESS",
            "WARNING",
            "ERROR",
            "CRITICAL",
        }

        if value not in allowed:
            raise ValueError(f"Invalid log level '{value}'")

        return value

    @field_validator(
        "default_crf",
    )
    @classmethod
    def validate_crf(
        cls,
        value: int,
    ) -> int:

        if not 0 <= value <= 51:
            raise ValueError("CRF must be between 0 and 51.")

        return value

    @field_validator(
        "vertical_width",
        "vertical_height",
    )
    @classmethod
    def validate_dimension(
        cls,
        value: int,
    ) -> int:

        if value <= 0:
            raise ValueError("Dimensions must be positive.")

        return value

    @field_validator(
        "ffmpeg_threads",
        "whisper_threads",
    )
    @classmethod
    def validate_threads(
        cls,
        value: int,
    ) -> int:

        return max(1, value)

    # ==========================================================
    # Helpers
    # ==========================================================

    @property
    def is_gpu_enabled(self) -> bool:
        return self.use_gpu

    @property
    def is_debug(self) -> bool:
        return self.debug

    @property
    def caption_style(self) -> dict:

        return {
            "font": self.caption_font,
            "font_size": self.caption_font_size,
            "stroke_width": self.caption_stroke_width,
            "max_words": self.caption_max_words,
            "bottom_margin": self.caption_bottom_margin,
        }

    # ==========================================================
    # Directory Creation
    # ==========================================================

    def ensure_directories(self) -> None:

        directories = [
            self.output_dir,
            self.cache_dir,
            self.temp_dir,
            self.logs_dir,
            self.config_dir,
            self.plugin_directory,
        ]

        for directory in directories:
            directory.mkdir(
                parents=True,
                exist_ok=True,
            )

    # ==========================================================
    # Convenience
    # ==========================================================

    def as_dict(self) -> dict:

        return self.model_dump()

    def reload(self) -> Settings:
        """
        Reload settings from environment.
        """
        return Settings()


# ======================================================================
# Singleton
# ======================================================================


@lru_cache(maxsize=1)
def get_settings() -> Settings:

    settings = Settings()

    settings.ensure_directories()

    return settings


settings = get_settings()
