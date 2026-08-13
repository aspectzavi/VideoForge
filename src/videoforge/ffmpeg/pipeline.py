
"""
VideoForge Pipeline Engine

The Pipeline orchestrates sequential processing steps.

The pipeline supports two compatible execution models:

1. PipelineStep
   Lightweight steps exposing:
       execute(context)

2. Operation
   Full VideoForge operations exposing:
       prepare(context)
       build_job(context)
       finalize(context)
       rollback(context, error)

PipelineStep / PipelineContext are intentionally kept as a lightweight
public API for simple pipelines, tests, experiments, and custom workflows.
"""

from __future__ import annotations

import time
from contextlib import suppress
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from videoforge.engine.dispatcher import dispatcher
from videoforge.engine.events import (
    PipelineCompletedEvent,
    PipelineFailedEvent,
    PipelineStartedEvent,
    ProgressEvent,
    StepCompletedEvent,
    StepStartedEvent,
)
from videoforge.ffmpeg.runner import FFmpegRunner
from videoforge.operations.base import Operation, OperationContext


# ==========================================================
# Pipeline Context
# ==========================================================


class PipelineContext:
    """
    Lightweight mutable context used by PipelineStep.

    Values can be shared between sequential steps.
    """

    def __init__(
        self,
        input_file: str | Path | None = None,
    ) -> None:
        self.input_file = (
            Path(input_file)
            if input_file is not None
            else None
        )

        self.values: dict[str, Any] = {}

        self.current_step: int = 0
        self.total_steps: int = 0
        self.cancelled: bool = False

    # ------------------------------------------------------

    def set(
        self,
        key: str,
        value: Any,
    ) -> None:
        """Store a value in the context."""

        self.values[key] = value

    # ------------------------------------------------------

    def get(
        self,
        key: str,
        default: Any = None,
    ) -> Any:
        """Retrieve a value from the context."""

        return self.values.get(key, default)

    # ------------------------------------------------------

    def has(
        self,
        key: str,
    ) -> bool:
        """Return True when a value exists."""

        return key in self.values

    # ------------------------------------------------------

    def remove(
        self,
        key: str,
    ) -> Any:
        """Remove and return a value."""

        return self.values.pop(key, None)

    # ------------------------------------------------------

    def clear(self) -> None:
        """Clear stored values."""

        self.values.clear()

    # ------------------------------------------------------

    def model_dump(self) -> dict[str, Any]:
        """
        Provide a model_dump-like representation for compatibility
        with existing examples/tests.
        """

        return {
            "input_file": self.input_file,
            "values": dict(self.values),
            "current_step": self.current_step,
            "total_steps": self.total_steps,
            "cancelled": self.cancelled,
        }


# ==========================================================
# Pipeline Step
# ==========================================================


class PipelineStep:
    """
    Lightweight pipeline step.

    Subclasses implement execute().
    """

    name: str = "Pipeline Step"

    def execute(
        self,
        context: PipelineContext,
    ) -> None:
        """
        Execute this step.

        Subclasses must override this method.
        """

        raise NotImplementedError(
            f"{self.__class__.__name__}.execute() must be implemented."
        )

    # ------------------------------------------------------

    @property
    def display_name(self) -> str:
        return self.name


# ==========================================================
# Pipeline Result
# ==========================================================


class PipelineResult(BaseModel):
    """
    Result returned after pipeline execution.
    """

    success: bool
    elapsed: float

    # Supports both the modern OperationContext and the
    # lightweight PipelineContext.
    context: Any


# ==========================================================
# Pipeline
# ==========================================================


class Pipeline:
    """
    Coordinates execution of a sequence of pipeline steps.

    Both PipelineStep and Operation objects are supported.
    """

    def __init__(self) -> None:
        self.steps: list[Any] = []
        self.runner = FFmpegRunner()

    # ------------------------------------------------------
    # Adding steps
    # ------------------------------------------------------

    def add(
        self,
        step: Any,
    ) -> Pipeline:
        """
        Add a PipelineStep or Operation.

        Returns self to allow:

            Pipeline().add(step1).add(step2)
        """

        self.steps.append(step)

        return self

    # ------------------------------------------------------

    @property
    def operations(self) -> list[Any]:
        """
        Compatibility alias for code using the newer
        Operation terminology.
        """

        return self.steps

    # ------------------------------------------------------

    def clear(self) -> None:
        """Remove every step."""

        self.steps.clear()

    # ------------------------------------------------------

    @property
    def step_count(self) -> int:
        return len(self.steps)

    # ======================================================
    # Execution
    # ======================================================

    def run(
        self,
        input_file: str | Path,
    ) -> PipelineResult:
        """
        Execute the pipeline.

        PipelineStep objects use PipelineContext.

        Operation objects use OperationContext.
        """

        if self._uses_pipeline_steps():
            return self._run_steps(input_file)

        return self._run_operations(input_file)

    # ======================================================
    # Lightweight PipelineStep execution
    # ======================================================

    def _run_steps(
        self,
        input_file: str | Path,
    ) -> PipelineResult:
        context = PipelineContext(
            input_file=input_file,
        )

        context.total_steps = len(self.steps)

        start = time.perf_counter()

        dispatcher.emit(
            PipelineStartedEvent(
                pipeline=self.__class__.__name__,
                steps=len(self.steps),
            )
        )

        try:
            for index, step in enumerate(
                self.steps,
                start=1,
            ):
                if context.cancelled:
                    break

                context.current_step = index

                name = getattr(
                    step,
                    "display_name",
                    getattr(
                        step,
                        "name",
                        step.__class__.__name__,
                    ),
                )

                dispatcher.emit(
                    StepStartedEvent(
                        index=index,
                        total=context.total_steps,
                        name=name,
                    )
                )

                step_start = time.perf_counter()

                step.execute(context)

                dispatcher.emit(
                    StepCompletedEvent(
                        index=index,
                        total=context.total_steps,
                        name=name,
                        elapsed=time.perf_counter() - step_start,
                    )
                )

        except Exception as exc:
            dispatcher.emit(
                PipelineFailedEvent(
                    error=str(exc),
                )
            )

            raise

        elapsed = time.perf_counter() - start

        dispatcher.emit(
            PipelineCompletedEvent(
                elapsed=elapsed,
            )
        )

        return PipelineResult(
            success=not context.cancelled,
            elapsed=elapsed,
            context=context,
        )

    # ======================================================
    # Modern Operation execution
    # ======================================================

    def _run_operations(
        self,
        input_file: str | Path,
    ) -> PipelineResult:
        context = OperationContext(
            input_file=Path(input_file),
            total_steps=len(self.steps),
        )

        start = time.perf_counter()

        dispatcher.emit(
            PipelineStartedEvent(
                pipeline=self.__class__.__name__,
                steps=len(self.steps),
            )
        )

        current_operation: Operation | None = None

        try:
            for index, operation in enumerate(
                self.steps,
                start=1,
            ):
                current_operation = operation

                if context.cancelled:
                    break

                context.current_step = index

                dispatcher.emit(
                    StepStartedEvent(
                        index=index,
                        total=context.total_steps,
                        name=operation.display_name,
                    )
                )

                step_start = time.perf_counter()

                operation.prepare(context)

                job = operation.build_job(context)

                if job is not None:
                    for progress in self.runner.run_stream(job):
                        dispatcher.emit(
                            ProgressEvent(
                                percentage=progress.percentage,
                                elapsed_seconds=progress.elapsed_seconds,
                                speed=progress.speed,
                                fps=progress.fps,
                                frame=progress.frame,
                                bitrate=progress.bitrate,
                                eta_seconds=progress.eta_seconds,
                            )
                        )

                operation.finalize(context)

                dispatcher.emit(
                    StepCompletedEvent(
                        index=index,
                        total=context.total_steps,
                        name=operation.display_name,
                        elapsed=time.perf_counter() - step_start,
                    )
                )

        except Exception as exc:
            dispatcher.emit(
                PipelineFailedEvent(
                    error=str(exc),
                )
            )

            if current_operation is not None:
                with suppress(Exception):
                    current_operation.rollback(
                        context,
                        exc,
                    )

            raise

        elapsed = time.perf_counter() - start

        dispatcher.emit(
            PipelineCompletedEvent(
                elapsed=elapsed,
            )
        )

        return PipelineResult(
            success=not context.cancelled,
            elapsed=elapsed,
            context=context,
        )

    # ======================================================
    # Helpers
    # ======================================================

    def _uses_pipeline_steps(self) -> bool:
        """
        Determine whether this pipeline contains lightweight
        PipelineStep objects.

        Mixed PipelineStep/Operation pipelines are intentionally
        rejected because the two context models are different.
        """

        if not self.steps:
            return True

        has_steps = any(
            isinstance(step, PipelineStep)
            for step in self.steps
        )

        has_operations = any(
            isinstance(step, Operation)
            for step in self.steps
        )

        if has_steps and has_operations:
            raise TypeError(
                "A Pipeline cannot mix PipelineStep and Operation "
                "objects in the same pipeline."
            )

        return has_steps
