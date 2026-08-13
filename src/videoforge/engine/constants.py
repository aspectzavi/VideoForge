"""
VideoForge Constants

Central location for project-wide constants, paths, defaults and
supported formats.
"""

from __future__ import annotations

import os
from pathlib import Path

# =====================================================================
# Project Paths
# =====================================================================

# src/videoforge/engine/constants.py
#                ↑
# parents[3] -> project root

PROJECT_ROOT = Path(__file__).resolve().parents[3]

SRC_DIR = PROJECT_ROOT / "src"

PACKAGE_DIR = SRC_DIR / "videoforge"

CONFIG_DIR = PROJECT_ROOT / "configs"

DOCS_DIR = PROJECT_ROOT / "docs"

TESTS_DIR = PROJECT_ROOT / "tests"

SCRIPTS_DIR = PROJECT_ROOT / "scripts"

CACHE_DIR = PROJECT_ROOT / "cache"

TEMP_DIR = PROJECT_ROOT / "temp"

LOGS_DIR = PROJECT_ROOT / "logs"

OUTPUT_DIR = PROJECT_ROOT / "output"

ASSETS_DIR = PACKAGE_DIR / "assets"

TEMPLATES_DIR = PACKAGE_DIR / "templates"

PLUGINS_DIR = PACKAGE_DIR / "plugins"

# =====================================================================
# AI Assets
# =====================================================================

MODELS_DIR = CACHE_DIR / "models"

WHISPER_MODELS_DIR = MODELS_DIR / "whisper"

MEDIAPIPE_MODELS_DIR = MODELS_DIR / "mediapipe"

# =====================================================================
# Configuration
# =====================================================================

DEFAULT_CONFIG_FILE = CONFIG_DIR / "config.yaml"

DEFAULT_ENV_FILE = PROJECT_ROOT / ".env"

# =====================================================================
# Executables
# =====================================================================

FFMPEG_EXECUTABLE = "ffmpeg"

FFPROBE_EXECUTABLE = "ffprobe"

FFPLAY_EXECUTABLE = "ffplay"

# =====================================================================
# Rendering Defaults
# =====================================================================

DEFAULT_VIDEO_CODEC = "libx264"

DEFAULT_AUDIO_CODEC = "aac"

DEFAULT_PIXEL_FORMAT = "yuv420p"

DEFAULT_PRESET = "medium"

DEFAULT_CRF = 20

DEFAULT_AUDIO_BITRATE = "192k"

DEFAULT_SAMPLE_RATE = 48_000

DEFAULT_FRAME_RATE = 30

DEFAULT_AUDIO_CHANNELS = 2

# =====================================================================
# Vertical Video Defaults
# =====================================================================

VERTICAL_WIDTH = 1080

VERTICAL_HEIGHT = 1920

VERTICAL_ASPECT = "9:16"

# =====================================================================
# Thumbnail Defaults
# =====================================================================

THUMBNAIL_WIDTH = 1280

THUMBNAIL_HEIGHT = 720

# =====================================================================
# Caption Defaults
# =====================================================================

DEFAULT_FONT = "Arial"

DEFAULT_FONT_SIZE = 56

DEFAULT_STROKE_WIDTH = 3

DEFAULT_MAX_WORDS = 4

DEFAULT_CAPTION_MARGIN = 120

# =====================================================================
# AI Defaults
# =====================================================================

DEFAULT_WHISPER_MODEL = "base"

DEFAULT_TRANSLATION_MODEL = "nllb"

DEFAULT_DEVICE = "cuda"

DEFAULT_COMPUTE_TYPE = "float16"

# =====================================================================
# File Extensions
# =====================================================================

VIDEO_EXTENSIONS = {
    ".mp4",
    ".mov",
    ".avi",
    ".mkv",
    ".webm",
    ".flv",
    ".m4v",
    ".mpeg",
    ".mpg",
}

AUDIO_EXTENSIONS = {
    ".mp3",
    ".wav",
    ".aac",
    ".m4a",
    ".ogg",
    ".opus",
    ".flac",
}

IMAGE_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".webp",
    ".bmp",
}

SUBTITLE_EXTENSIONS = {
    ".srt",
    ".vtt",
    ".ass",
    ".ssa",
}

# =====================================================================
# Social Media Presets
# =====================================================================

SOCIAL_PRESETS = {
    "tiktok": (1080, 1920),
    "reels": (1080, 1920),
    "shorts": (1080, 1920),
    "facebook": (1080, 1350),
    "instagram": (1080, 1080),
    "twitter": (1280, 720),
}

# =====================================================================
# Environment Variables
# =====================================================================

ENV_DEBUG = "VIDEOFORGE_DEBUG"

ENV_LOG_LEVEL = "VIDEOFORGE_LOG_LEVEL"

ENV_FFMPEG = "VIDEOFORGE_FFMPEG"

ENV_FFPROBE = "VIDEOFORGE_FFPROBE"

ENV_CACHE = "VIDEOFORGE_CACHE"

# =====================================================================
# Miscellaneous
# =====================================================================

APP_NAME = "VideoForge"

APP_AUTHOR = "Kevin Kamau"

APP_VERSION = "0.1.0"

DEFAULT_ENCODING = "utf-8"

CHUNK_SIZE = 1024 * 1024

SECONDS_PER_MINUTE = 60

MICROSECONDS = 1_000_000

# =====================================================================
# Create Required Directories
# =====================================================================

_REQUIRED_DIRS = (
    CACHE_DIR,
    CONFIG_DIR,
    LOGS_DIR,
    OUTPUT_DIR,
    TEMP_DIR,
    MODELS_DIR,
)

for directory in _REQUIRED_DIRS:
    directory.mkdir(
        parents=True,
        exist_ok=True,
    )

# =====================================================================
# Debug Mode
# =====================================================================

DEBUG = os.getenv(
    ENV_DEBUG,
    "false",
).lower() in {
    "1",
    "true",
    "yes",
}
