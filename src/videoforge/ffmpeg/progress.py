"""
FFmpeg progress parsing utilities.
"""

from __future__ import annotations

from collections.abc import Iterable

from pydantic import BaseModel, computed_field

# =====================================================================
# Progress Information
# =====================================================================


class ProgressInfo(BaseModel):
    """
    Current state of an FFmpeg job.
    """

    frame: int | None = None

    fps: float | None = None

    bitrate: str | None = None

    out_time_us: int | None = None

    out_time_ms: int | None = None

    out_time: str | None = None

    speed: str | None = None

    progress: str | None = None

    total_duration: float | None = None

    # -------------------------------------------------------------

    @computed_field
    @property
    def elapsed_seconds(self) -> float:

        if self.out_time_ms is not None:
            return self.out_time_ms / 1_000_000

        if self.out_time_us is not None:
            return self.out_time_us / 1_000_000

        return 0.0

    # -------------------------------------------------------------

    @computed_field
    @property
    def percentage(self) -> float:

        if not self.total_duration:
            return 0.0

        if self.total_duration <= 0:
            return 0.0

        pct = (self.elapsed_seconds / self.total_duration) * 100.0

        return round(
            max(
                0.0,
                min(100.0, pct),
            ),
            2,
        )

    # -------------------------------------------------------------

    @computed_field
    @property
    def remaining_seconds(self) -> float:

        if not self.total_duration:
            return 0.0

        return max(
            0.0,
            self.total_duration - self.elapsed_seconds,
        )

    # -------------------------------------------------------------

    @computed_field
    @property
    def eta_seconds(self) -> float | None:
        """
        Estimated remaining wall-clock time.
        """

        if not self.speed:
            return None

        try:
            speed = float(self.speed.lower().replace("x", ""))

        except ValueError:
            return None

        if speed <= 0:
            return None

        return round(
            self.remaining_seconds / speed,
            2,
        )

    # -------------------------------------------------------------

    @computed_field
    @property
    def is_running(self) -> bool:

        return self.progress == "continue"

    # -------------------------------------------------------------

    @computed_field
    @property
    def is_finished(self) -> bool:

        return self.progress == "end"

    # -------------------------------------------------------------

    @computed_field
    @property
    def is_failed(self) -> bool:

        return self.progress == "error"

    # -------------------------------------------------------------

    @computed_field
    @property
    def speed_multiplier(self) -> float | None:

        if not self.speed:
            return None

        try:
            return float(self.speed.lower().replace("x", ""))

        except ValueError:
            return None


# =====================================================================
# Progress Parser
# =====================================================================


class ProgressParser:
    """
    Parses FFmpeg -progress output.

    Example input:

        frame=123
        fps=59.94
        out_time_ms=5000000
        speed=2.10x
        progress=continue
    """

    def __init__(
        self,
        total_duration: float | None = None,
    ) -> None:

        self.total_duration = total_duration

        self._data: dict[str, str] = {}

    # -------------------------------------------------------------

    def reset(self) -> None:

        self._data.clear()

    # -------------------------------------------------------------

    def feed(
        self,
        line: str,
    ) -> ProgressInfo | None:

        line = line.strip()

        if not line:
            return None

        if "=" not in line:
            return None

        key, value = line.split(
            "=",
            1,
        )

        self._data[key] = value

        if key != "progress":
            return None

        progress = ProgressInfo(
            frame=self._to_int(self._data.get("frame")),
            fps=self._to_float(self._data.get("fps")),
            bitrate=self._data.get("bitrate"),
            out_time=self._data.get("out_time"),
            out_time_ms=self._to_int(self._data.get("out_time_ms")),
            out_time_us=self._to_int(self._data.get("out_time_us")),
            speed=self._data.get("speed"),
            progress=self._data.get("progress"),
            total_duration=self.total_duration,
        )

        self.reset()

        return progress

    # -------------------------------------------------------------

    def parse(
        self,
        lines: Iterable[str],
    ):

        for line in lines:
            progress = self.feed(line)

            if progress is not None:
                yield progress

    # -------------------------------------------------------------

    @staticmethod
    def _to_int(
        value: str | None,
    ) -> int | None:

        if value in (
            None,
            "",
            "N/A",
        ):
            return None

        try:
            return int(value)

        except ValueError:
            return None

    # -------------------------------------------------------------

    @staticmethod
    def _to_float(
        value: str | None,
    ) -> float | None:

        if value in (
            None,
            "",
            "N/A",
        ):
            return None

        try:
            return float(value)

        except ValueError:
            return None


# Backwards compatibility
FFmpegProgressParser = ProgressParser
