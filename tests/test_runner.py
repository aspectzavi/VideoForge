"""
Fast, mocked unit tests for FFmpegRunner.

subprocess.Popen / subprocess.run are mocked throughout, so these
tests never spawn a real FFmpeg process. They exercise:

- normal streaming success
- non-zero exit -> FFmpegExecutionError (with stderr captured despite
  never being read directly by the main thread — see runner.py)
- cancellation via a threading.Event -> PipelineCancelledError
- watchdog timeout -> FFmpegTimeoutError, independent of stdout activity
- process start failure -> FFmpegExecutionError
- run_capture's equivalent timeout / failure / start-failure paths
- that the process is never left running (kill() is always reached)

See tests/integration/test_runner_integration.py for the real-FFmpeg
equivalents of cancellation and timeout.
"""

from __future__ import annotations

import subprocess
import threading
import time
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from videoforge.engine.exceptions import (
    FFmpegExecutionError,
    FFmpegTimeoutError,
    PipelineCancelledError,
)
from videoforge.ffmpeg.job import FFmpegJob
from videoforge.ffmpeg.runner import FFmpegRunner


@pytest.fixture
def job(tmp_path: Path) -> FFmpegJob:
    input_file = tmp_path / "input.mp4"
    input_file.write_bytes(b"not a real video, just needs to exist")

    return FFmpegJob(
        inputs=[input_file],
        output=tmp_path / "output.mp4",
    )


def _mock_process(
    stdout_lines: list[str],
    stderr_lines: list[str],
    return_code: int = 0,
) -> MagicMock:
    process = MagicMock()
    # Real subprocess.Popen pipes are file objects with .close(); a
    # plain list_iterator (iter([...])) doesn't have one. Generator
    # expressions do support .close(), so use those to match the real
    # interface the runner's cleanup code relies on.
    process.stdout = (line for line in stdout_lines)
    process.stderr = (line for line in stderr_lines)
    process.wait.return_value = return_code
    process.poll.return_value = return_code
    return process


# ---------------------------------------------------------------------
# run_stream: normal success
# ---------------------------------------------------------------------


def test_run_stream_yields_progress_and_succeeds(job: FFmpegJob) -> None:
    stdout_lines = [
        "frame=10\n",
        "fps=24.0\n",
        "out_time_ms=1000000\n",
        "speed=1.0x\n",
        "progress=end\n",
    ]
    process = _mock_process(stdout_lines, [], return_code=0)

    with patch(
        "videoforge.ffmpeg.runner.subprocess.Popen",
        return_value=process,
    ):
        runner = FFmpegRunner()
        results = list(runner.run_stream(job))

    assert len(results) == 1
    assert results[0].frame == 10
    assert results[0].is_finished is True
    process.wait.assert_called_once()


# ---------------------------------------------------------------------
# run_stream: non-zero exit code
# ---------------------------------------------------------------------


def test_run_stream_raises_on_nonzero_exit(job: FFmpegJob) -> None:
    process = _mock_process(
        stdout_lines=[],
        stderr_lines=["Error: something went wrong\n"],
        return_code=1,
    )

    with patch(
        "videoforge.ffmpeg.runner.subprocess.Popen",
        return_value=process,
    ):
        runner = FFmpegRunner()

        with pytest.raises(FFmpegExecutionError, match="something went wrong"):
            list(runner.run_stream(job))


# ---------------------------------------------------------------------
# run_stream: process fails to start
# ---------------------------------------------------------------------


def test_run_stream_raises_when_process_fails_to_start(job: FFmpegJob) -> None:
    with patch(
        "videoforge.ffmpeg.runner.subprocess.Popen",
        side_effect=OSError("executable not found"),
    ):
        runner = FFmpegRunner()

        with pytest.raises(FFmpegExecutionError, match="Failed to start"):
            list(runner.run_stream(job))


# ---------------------------------------------------------------------
# run_stream: cancellation
# ---------------------------------------------------------------------


def test_run_stream_cancellation_kills_process_and_raises(job: FFmpegJob) -> None:
    stdout_lines = [
        "frame=1\n",
        "progress=continue\n",
        "frame=2\n",
        "progress=continue\n",
    ]
    process = _mock_process(stdout_lines, [], return_code=0)

    cancel_event = threading.Event()
    cancel_event.set()  # already cancelled before the loop starts

    with patch(
        "videoforge.ffmpeg.runner.subprocess.Popen",
        return_value=process,
    ):
        runner = FFmpegRunner()

        with pytest.raises(PipelineCancelledError):
            list(runner.run_stream(job, cancel_event=cancel_event))

    assert process.kill.called


# ---------------------------------------------------------------------
# run_stream: watchdog timeout
# ---------------------------------------------------------------------


def test_run_stream_timeout_kills_process_and_raises(job: FFmpegJob) -> None:
    def _stuck_stdout():
        # Simulates FFmpeg producing no output at all for longer than
        # the timeout — nothing to iterate over except a delay.
        time.sleep(0.2)
        return
        yield  # pragma: no cover - makes this a generator

    process = MagicMock()
    process.stdout = _stuck_stdout()
    process.stderr = (line for line in [])
    process.wait.return_value = 0
    process.poll.return_value = None

    with patch(
        "videoforge.ffmpeg.runner.subprocess.Popen",
        return_value=process,
    ):
        runner = FFmpegRunner()

        with pytest.raises(FFmpegTimeoutError):
            list(runner.run_stream(job, timeout=0.05))

    assert process.kill.called


# ---------------------------------------------------------------------
# run_stream: process is never left running (cleanup guarantee)
# ---------------------------------------------------------------------


def test_run_stream_kills_process_if_still_alive_on_exception(
    job: FFmpegJob,
) -> None:
    """
    Even on an unexpected exception mid-stream, the finally block must
    still attempt to kill/wait on the process rather than leaking it.
    """

    def _raising_stdout():
        yield "frame=1\n"
        raise RuntimeError("simulated parser/consumer crash")

    process = MagicMock()
    process.stdout = _raising_stdout()
    process.stderr = (line for line in [])
    process.wait.return_value = 0
    process.poll.return_value = None  # still "running" when exception hits

    with patch(
        "videoforge.ffmpeg.runner.subprocess.Popen",
        return_value=process,
    ):
        runner = FFmpegRunner()

        with pytest.raises(RuntimeError, match="simulated parser"):
            list(runner.run_stream(job))

    assert process.kill.called


# ---------------------------------------------------------------------
# run_capture
# ---------------------------------------------------------------------


def test_run_capture_success(job: FFmpegJob) -> None:
    completed = subprocess.CompletedProcess(
        args=["ffmpeg"],
        returncode=0,
        stdout="",
        stderr="",
    )

    with patch(
        "videoforge.ffmpeg.runner.subprocess.run",
        return_value=completed,
    ):
        runner = FFmpegRunner()
        result = runner.run_capture(job)

    assert result.returncode == 0


def test_run_capture_raises_on_timeout(job: FFmpegJob) -> None:
    with patch(
        "videoforge.ffmpeg.runner.subprocess.run",
        side_effect=subprocess.TimeoutExpired(cmd=["ffmpeg"], timeout=5),
    ):
        runner = FFmpegRunner()

        with pytest.raises(FFmpegTimeoutError):
            runner.run_capture(job, timeout=5)


def test_run_capture_raises_on_nonzero_exit(job: FFmpegJob) -> None:
    error = subprocess.CalledProcessError(
        returncode=1,
        cmd=["ffmpeg"],
        stderr="boom",
    )

    with patch(
        "videoforge.ffmpeg.runner.subprocess.run",
        side_effect=error,
    ):
        runner = FFmpegRunner()

        with pytest.raises(FFmpegExecutionError, match="boom"):
            runner.run_capture(job)


def test_run_capture_raises_when_process_fails_to_start(job: FFmpegJob) -> None:
    with patch(
        "videoforge.ffmpeg.runner.subprocess.run",
        side_effect=OSError("executable not found"),
    ):
        runner = FFmpegRunner()

        with pytest.raises(FFmpegExecutionError, match="Failed to start"):
            runner.run_capture(job)
