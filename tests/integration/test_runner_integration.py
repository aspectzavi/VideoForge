"""
Integration tests for FFmpegRunner cancellation and timeout, using a
real FFmpeg subprocess (unlike tests/test_runner.py, which mocks
subprocess.Popen entirely).

These are tagged @pytest.mark.integration and deliberately fast: both
scenarios interrupt the encode early rather than letting it run to
completion, unlike tests/test_vertical.py::test_vertical_crop which
lets a full conversion finish (~60s).
"""

from __future__ import annotations

import threading
import time
from pathlib import Path

import pytest

from videoforge.engine.exceptions import (
    FFmpegTimeoutError,
    PipelineCancelledError,
)
from videoforge.ffmpeg.job import FFmpegJob
from videoforge.ffmpeg.runner import FFmpegRunner

SAMPLE_INPUT = Path("tests/sample_media/input.mp4")


def _slow_job(output: Path) -> FFmpegJob:
    """
    A deliberately slow-to-encode job so timeout/cancellation land
    mid-stream rather than racing a near-instant completion.
    """

    return FFmpegJob(
        inputs=[SAMPLE_INPUT],
        output=output,
        video_codec="libx264",
        audio_codec="aac",
        preset="veryslow",
        crf=18,
    )


@pytest.mark.integration
def test_real_ffmpeg_timeout_is_enforced(tmp_path: Path) -> None:
    output = tmp_path / "timeout_out.mp4"
    job = _slow_job(output)
    runner = FFmpegRunner()

    start = time.perf_counter()

    with pytest.raises(FFmpegTimeoutError):
        list(runner.run_stream(job, timeout=2.0))

    elapsed = time.perf_counter() - start

    # A veryslow/crf18 encode of the sample clip takes well over a
    # minute uninterrupted (see test_vertical.py). If the watchdog
    # worked, this returns in a few seconds, not anywhere near that.
    assert elapsed < 15.0


@pytest.mark.integration
def test_real_ffmpeg_cancellation_stops_early(tmp_path: Path) -> None:
    output = tmp_path / "cancel_out.mp4"
    job = _slow_job(output)
    runner = FFmpegRunner()

    cancel_event = threading.Event()
    start = time.perf_counter()

    gen = runner.run_stream(job, cancel_event=cancel_event)

    # Let at least one real progress update come through, proving the
    # process was genuinely running, then cancel.
    next(gen)
    cancel_event.set()

    with pytest.raises(PipelineCancelledError):
        for _ in gen:
            pass

    elapsed = time.perf_counter() - start

    assert elapsed < 15.0
