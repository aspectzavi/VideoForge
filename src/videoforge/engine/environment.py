"""
Environment detection utilities for VideoForge.
"""

from __future__ import annotations

import platform
import shutil
from pathlib import Path

import psutil
from pydantic import BaseModel


class EnvironmentInfo(BaseModel):
    """Represents the current runtime environment."""

    operating_system: str
    os_version: str
    machine: str

    python_version: str

    cpu: str
    cpu_cores: int
    logical_cores: int

    ram_gb: float

    ffmpeg_installed: bool
    ffprobe_installed: bool

    ffmpeg_path: str | None
    ffprobe_path: str | None

    project_root: Path
    cwd: Path


def detect_environment() -> EnvironmentInfo:
    """Collect information about the current environment."""

    memory = psutil.virtual_memory()

    ffmpeg = shutil.which("ffmpeg")
    ffprobe = shutil.which("ffprobe")

    return EnvironmentInfo(
        operating_system=platform.system(),
        os_version=platform.version(),
        machine=platform.machine(),
        python_version=platform.python_version(),
        cpu=platform.processor(),
        cpu_cores=psutil.cpu_count(logical=False) or 0,
        logical_cores=psutil.cpu_count(logical=True) or 0,
        ram_gb=round(memory.total / (1024**3), 2),
        ffmpeg_installed=ffmpeg is not None,
        ffprobe_installed=ffprobe is not None,
        ffmpeg_path=ffmpeg,
        ffprobe_path=ffprobe,
        project_root=Path.cwd(),
        cwd=Path.cwd(),
    )


def ffmpeg_available() -> bool:
    """Return True if both FFmpeg and FFprobe are available."""

    env = detect_environment()

    return env.ffmpeg_installed and env.ffprobe_installed
