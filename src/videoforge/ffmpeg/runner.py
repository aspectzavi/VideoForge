"""
VideoForge FFmpeg Runner

Responsible only for executing FFmpeg jobs and streaming progress.

Responsibilities
----------------
- Validate jobs
- Build FFmpeg command
- Execute FFmpeg
- Parse progress
- Yield ProgressInfo objects

Does NOT:
- Log
- Emit events
- Update pipeline context
"""

from __future__ import annotations

import subprocess
import threading
from collections.abc import Iterator

from videoforge.engine.exceptions import (
    FFmpegExecutionError,
    FFmpegTimeoutError,
    PipelineCancelledError,
)
from videoforge.ffmpeg.command import FFmpegCommandBuilder
from videoforge.ffmpeg.job import FFmpegJob
from videoforge.ffmpeg.progress import ProgressInfo, ProgressParser
from videoforge.ffmpeg.validation import JobValidator


class FFmpegRunner:
    """
    Execute FFmpeg jobs.

    The runner is intentionally UI-agnostic.
    It only yields ProgressInfo objects.
    """

    # ---------------------------------------------------------

    def run(
        self,
        job: FFmpegJob,
        timeout: float | None = None,
        cancel_event: threading.Event | None = None,
    ) -> None:
        """
        Execute a job without consuming progress.
        """

        for _ in self.run_stream(job, timeout=timeout, cancel_event=cancel_event):
            pass

    # ---------------------------------------------------------

    def run_stream(
        self,
        job: FFmpegJob,
        timeout: float | None = None,
        cancel_event: threading.Event | None = None,
    ) -> Iterator[ProgressInfo]:
        """
        Execute FFmpeg and yield ProgressInfo objects.

        Parameters
        ----------
        timeout
            Maximum wall-clock seconds to allow the FFmpeg process to
            run. Enforced by a background watchdog timer so it applies
            even if FFmpeg produces no progress output at all (e.g. a
            genuinely stuck process, not just a slow one). Raises
            FFmpegTimeoutError and guarantees the process is killed.

        cancel_event
            An externally-controlled threading.Event. If set while the
            job is running, the process is killed and
            PipelineCancelledError is raised. Checked once per progress
            line, which is sufficient for graceful cancellation since
            FFmpeg emits progress lines frequently during encoding.
        """

        JobValidator.validate(job)

        command = self._build_progress_command(job)

        try:
            process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                stdin=subprocess.DEVNULL,
                text=True,
                universal_newlines=True,
                bufsize=1,
            )
        except OSError as exc:
            raise FFmpegExecutionError(
                f"Failed to start FFmpeg process: {exc}"
            ) from exc

        parser = ProgressParser()

        assert process.stdout is not None
        assert process.stderr is not None

        # FFmpeg writes its banner, stream mapping, and per-line
        # diagnostics to stderr while progress goes to stdout (see
        # _build_progress_command). Both are OS pipes with a small
        # fixed buffer (64KB on Windows). If we only drain stdout in
        # this thread, stderr fills up once FFmpeg logs enough output,
        # FFmpeg blocks on the write() syscall, and since it is a
        # single process that also stops producing stdout progress -
        # a full deadlock. We drain stderr concurrently on a background
        # thread so FFmpeg is never blocked writing to either pipe.
        stderr_lines: list[str] = []

        def _drain_stderr() -> None:
            assert process.stderr is not None
            for line in process.stderr:
                stderr_lines.append(line)

        stderr_thread = threading.Thread(
            target=_drain_stderr,
            daemon=True,
        )
        stderr_thread.start()

        # Watchdog: enforced independently of stdout activity, so a
        # process that produces no progress output at all is still
        # bounded, not just a slow-but-ticking encode.
        timed_out = threading.Event()
        watchdog: threading.Timer | None = None

        if timeout is not None:

            def _on_timeout() -> None:
                timed_out.set()
                if process.poll() is None:
                    process.kill()

            watchdog = threading.Timer(timeout, _on_timeout)
            watchdog.daemon = True
            watchdog.start()

        cancelled = False

        try:
            for line in process.stdout:
                if cancel_event is not None and cancel_event.is_set():
                    cancelled = True
                    process.kill()
                    break

                progress = parser.feed(line)

                if progress is not None:
                    yield progress

            return_code = process.wait()
            stderr_thread.join(timeout=5)

            if timed_out.is_set():
                raise FFmpegTimeoutError(
                    f"FFmpeg exceeded timeout of {timeout}s and was killed."
                )

            if cancelled:
                raise PipelineCancelledError(
                    "FFmpeg job was cancelled before completion."
                )

            if return_code != 0:
                stderr = "".join(stderr_lines)
                raise FFmpegExecutionError(
                    stderr.strip() or f"FFmpeg exited with exit code {return_code}"
                )

        finally:
            if watchdog is not None:
                watchdog.cancel()

            if process.poll() is None:
                process.kill()
                process.wait()

            stderr_thread.join(timeout=5)

            if process.stdout:
                process.stdout.close()

            if process.stderr:
                process.stderr.close()

    # ---------------------------------------------------------

    def run_capture(
        self,
        job: FFmpegJob,
        timeout: float | None = None,
    ) -> subprocess.CompletedProcess[str]:
        """
        Execute a job and return CompletedProcess.

        Useful for FFmpeg commands that don't require progress
        reporting. subprocess.run consumes stdout/stderr itself via
        communicate(), so this path is not subject to the pipe
        deadlock that run_stream guards against — but it can still
        hang indefinitely on a stuck process, hence the optional
        timeout.
        """

        JobValidator.validate(job)

        command = FFmpegCommandBuilder.build(job)

        try:
            return subprocess.run(
                command,
                capture_output=True,
                text=True,
                check=True,
                timeout=timeout,
            )

        except subprocess.TimeoutExpired as exc:
            raise FFmpegTimeoutError(
                f"FFmpeg exceeded timeout of {timeout}s and was killed."
            ) from exc

        except subprocess.CalledProcessError as exc:
            raise FFmpegExecutionError(exc.stderr.strip() or str(exc)) from exc

        except OSError as exc:
            raise FFmpegExecutionError(
                f"Failed to start FFmpeg process: {exc}"
            ) from exc

    # ---------------------------------------------------------

    @staticmethod
    def _build_progress_command(
        job: FFmpegJob,
    ) -> list[str]:
        """
        Build a command with FFmpeg progress enabled.

        FFmpeg requires global options to appear before the output file.
        """

        command = FFmpegCommandBuilder.build(job)

        output = command.pop()

        command.extend(
            [
                "-progress",
                "pipe:1",
                "-nostats",
            ]
        )

        command.append(output)

        return command
