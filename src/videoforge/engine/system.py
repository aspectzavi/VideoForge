"""
VideoForge System Information

Detects the host system capabilities and exposes them through a simple API.

Features
--------
- Operating system information
- CPU information
- RAM
- Python version
- FFmpeg / FFprobe detection
- NVIDIA / CUDA detection
- Hardware encoder detection
- Hardware decoder detection
"""

from __future__ import annotations

import platform
import shutil
import subprocess
from functools import lru_cache
from pathlib import Path

import psutil
from pydantic import BaseModel, computed_field

from videoforge.ffmpeg.binaries import BINARIES

# ==========================================================
# Model
# ==========================================================


class SystemInfo(BaseModel):
    operating_system: str

    os_version: str

    machine: str

    architecture: str

    python_version: str

    cpu: str

    cpu_cores: int

    logical_cores: int

    ram_gb: float

    ffmpeg: Path | None

    ffprobe: Path | None

    cuda: bool

    nvenc: bool

    qsv: bool

    amf: bool

    videotoolbox: bool

    project_root: Path

    cwd: Path

    # -----------------------------------------------------

    @computed_field
    @property
    def ffmpeg_installed(self) -> bool:

        return self.ffmpeg is not None

    @computed_field
    @property
    def ffprobe_installed(self) -> bool:

        return self.ffprobe is not None

    @computed_field
    @property
    def gpu_available(self) -> bool:

        return self.cuda or self.nvenc or self.qsv or self.amf or self.videotoolbox

    @computed_field
    @property
    def best_h264_encoder(self) -> str:

        if self.nvenc:
            return "h264_nvenc"

        if self.qsv:
            return "h264_qsv"

        if self.amf:
            return "h264_amf"

        if self.videotoolbox:
            return "h264_videotoolbox"

        return "libx264"

    @computed_field
    @property
    def best_hevc_encoder(self) -> str:

        if self.nvenc:
            return "hevc_nvenc"

        if self.qsv:
            return "hevc_qsv"

        if self.amf:
            return "hevc_amf"

        if self.videotoolbox:
            return "hevc_videotoolbox"

        return "libx265"


# ==========================================================
# Detector
# ==========================================================


class SystemDetector:
    # -----------------------------------------------------

    def detect(self) -> SystemInfo:

        return SystemInfo(
            operating_system=platform.system(),
            os_version=platform.version(),
            machine=platform.machine(),
            architecture=platform.architecture()[0],
            python_version=platform.python_version(),
            cpu=platform.processor(),
            cpu_cores=psutil.cpu_count(logical=False) or 1,
            logical_cores=psutil.cpu_count(logical=True) or 1,
            ram_gb=round(
                psutil.virtual_memory().total / (1024**3),
                2,
            ),
            ffmpeg=self._binary(BINARIES.ffmpeg),
            ffprobe=self._binary(BINARIES.ffprobe),
            cuda=self._detect_cuda(),
            nvenc=self._detect_encoder("h264_nvenc"),
            qsv=self._detect_encoder("h264_qsv"),
            amf=self._detect_encoder("h264_amf"),
            videotoolbox=self._detect_encoder("h264_videotoolbox"),
            project_root=Path.cwd(),
            cwd=Path.cwd(),
        )

    # -----------------------------------------------------

    @staticmethod
    def _binary(
        path: Path | str | None,
    ) -> Path | None:

        if path is None:
            return None

        path = Path(path)

        if path.exists():
            return path

        found = shutil.which(str(path))

        if found:
            return Path(found)

        return None

    # -----------------------------------------------------

    @staticmethod
    def _detect_cuda() -> bool:
        try:
            subprocess.run(
                ["nvidia-smi"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=True,
            )
        except (
            subprocess.CalledProcessError,
            FileNotFoundError,
            OSError,
        ):
            return False

        return True

    # -----------------------------------------------------

    @staticmethod
    def _detect_encoder(
        encoder: str,
    ) -> bool:
        try:
            result = subprocess.run(
                [
                    str(BINARIES.ffmpeg),
                    "-hide_banner",
                    "-encoders",
                ],
                capture_output=True,
                text=True,
                check=True,
            )
        except (
            subprocess.CalledProcessError,
            FileNotFoundError,
            OSError,
        ):
            return False

        return encoder in result.stdout


# ==========================================================
# Singleton
# ==========================================================


@lru_cache(maxsize=1)
def get_system() -> SystemInfo:

    return SystemDetector().detect()


system = get_system()
