
from __future__ import annotations

import time

from videoforge.engine.logger import logger


def test_logger_timer() -> None:
    """
    Verify that the logger.timer context manager executes
    the wrapped code without raising an exception.
    """

    with logger.timer("Sleeping"):
        time.sleep(0.01)


def test_logger_basic_logging() -> None:
    """
    Verify the standard Loguru logging methods used by VideoForge.
    """

    logger.debug("Debug test")
    logger.info("Info test")
    logger.warning("Warning test")
    logger.error("Error test")
    logger.success("Success test")


def test_logger_timer_preserves_exceptions() -> None:
    """
    Verify that timer does not suppress exceptions raised
    inside the managed block.
    """

    try:
        with logger.timer("Failing operation"):
            raise ValueError("test error")
    except ValueError as exc:
        assert str(exc) == "test error"
    else:
        raise AssertionError("ValueError was unexpectedly suppressed")
