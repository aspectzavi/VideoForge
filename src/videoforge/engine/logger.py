
"""
VideoForge Logging.

Central logging utilities.

This module configures Loguru and subscribes to the global event
dispatcher so that pipeline events are automatically logged.
"""

from __future__ import annotations

import time
from contextlib import contextmanager
from collections.abc import Iterator
import sys
from typing import Callable

from loguru import logger as _logger

from videoforge.engine.constants import LOGS_DIR
from videoforge.engine.dispatcher import dispatcher
from videoforge.engine.events import (
    Event,
    ExportCompletedEvent,
    ExportFailedEvent,
    ExportStartedEvent,
    PipelineCancelledEvent,
    PipelineCompletedEvent,
    PipelineFailedEvent,
    PipelineStartedEvent,
    ProgressEvent,
    StepCompletedEvent,
    StepFailedEvent,
    StepStartedEvent,
)


# =====================================================================
# Configure Loguru
# =====================================================================

LOG_FILE = LOGS_DIR / "videoforge.log"

_logger.remove()

_logger.add(
    sys.stdout,
    level="INFO",
    colorize=True,
    format=(
        "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
        "<level>{level:<8}</level> | {message}"
    ),
)

_logger.add(
    LOG_FILE,
    rotation="10 MB",
    retention=10,
    compression="zip",
    level="DEBUG",
    encoding="utf-8",
)


logger = _logger


# =====================================================================
# Timer Support
# =====================================================================


@contextmanager
def _timer(name: str) -> Iterator[None]:
    """
    Measure and log the execution time of a code block.

    Example
    -------
    with logger.timer("Processing"):
        process_video()
    """

    start = time.perf_counter()

    logger.info(f"{name} started")

    try:
        yield
    finally:
        elapsed = time.perf_counter() - start
        logger.success(f"{name} completed in {elapsed:.2f}s")


# Attach the helper to the Loguru logger instance so the existing
# VideoForge API remains:
#
#     with logger.timer("Something"):
#         ...
#
# This preserves logger.info(), logger.debug(), logger.success(), etc.
setattr(logger, "timer", _timer)


# =====================================================================
# Progress throttling
# =====================================================================

_last_percentage = -1


# =====================================================================
# Event Handler
# =====================================================================


def log_event(event: Event) -> None:
    """
    Log events emitted by the dispatcher.
    """

    global _last_percentage

    match event:
        # ----------------------------------------------------------
        # Pipeline
        # ----------------------------------------------------------

        case PipelineStartedEvent():
            logger.info(f"Starting pipeline ({event.steps} steps)")

        case PipelineCompletedEvent():
            logger.success(f"Pipeline completed in {event.elapsed:.2f}s")

        case PipelineCancelledEvent():
            logger.warning(f"Pipeline cancelled: {event.reason}")

        case PipelineFailedEvent():
            logger.error(f"Pipeline failed: {event.error}")

        # ----------------------------------------------------------
        # Steps
        # ----------------------------------------------------------

        case StepStartedEvent():
            logger.info(f"[{event.index}/{event.total}] {event.name}")

        case StepCompletedEvent():
            logger.success(
                f"{event.name} completed ({event.elapsed:.2f}s)"
            )

        case StepFailedEvent():
            logger.error(
                f"{event.name} failed: {event.error}"
            )

        # ----------------------------------------------------------
        # FFmpeg Progress
        # ----------------------------------------------------------

        case ProgressEvent():
            pct = int(event.percentage)

            # Avoid flooding the console.
            if pct == _last_percentage:
                return

            _last_percentage = pct

            speed = event.speed or "--"

            eta = (
                f"{event.eta_seconds:.1f}s"
                if event.eta_seconds is not None
                else "--"
            )

            fps = (
                f"{event.fps:.1f}"
                if event.fps is not None
                else "--"
            )

            logger.info(
                f"{event.percentage:6.2f}% | "
                f"ETA {eta} | "
                f"{speed} | "
                f"{fps} FPS"
            )

        # ----------------------------------------------------------
        # Export
        # ----------------------------------------------------------

        case ExportStartedEvent():
            logger.info(f"Exporting -> {event.output}")

        case ExportCompletedEvent():
            logger.success(
                f"Export completed ({event.elapsed:.2f}s)"
            )

        case ExportFailedEvent():
            logger.error(
                f"Export failed: {event.error}"
            )

        # ----------------------------------------------------------
        # Everything else
        # ----------------------------------------------------------

        case _:
            logger.debug(
                event.model_dump_json(indent=2)
            )


# =====================================================================
# Registration
# =====================================================================

dispatcher.subscribe_all(log_event)
