"""
Base classes for VideoForge operations.

An Operation represents one unit of work in a pipeline.

Operations DO NOT execute FFmpeg.
They prepare context, optionally build an FFmpegJob,
and finalize after execution.
"""

from __future__ import annotations

import tempfile
import uuid
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from videoforge.ffmpeg.job import FFmpegJob

# =====================================================================
# Pipeline Context
# =====================================================================


class OperationContext(BaseModel):
    """
    Shared state passed between operations.
    """

    input_file: Path

    output_file: Path | None = None

    media_info: Any | None = None

    data: dict[str, Any] = Field(default_factory=dict)

    cancelled: bool = False

    current_step: int = 0

    total_steps: int = 0

    # -----------------------------------------------------------------

    def next_output(
        self,
        suffix: str | None = None,
    ) -> Path:
        """
        Generate the next temporary output file.

        If no suffix is supplied, reuse the current input extension.
        """

        if suffix is None:
            suffix = self.input_file.suffix

        output = (
            Path(tempfile.gettempdir())
            / f"videoforge_{uuid.uuid4().hex}{suffix}"
        )

        self.output_file = output

        return output

    # -----------------------------------------------------------------

    def advance(self) -> None:
        """
        Promote the latest output to become the next input.
        """

        if self.output_file is None:
            return

        self.input_file = self.output_file
        self.output_file = None

    # -----------------------------------------------------------------

    @property
    def has_output(self) -> bool:
        return self.output_file is not None

    def set(
        self,
        key: str,
        value: Any,
    ) -> None:
        """
        Store a value in the shared operation context.

        Values remain available to subsequent operations
        in the same pipeline run.
        """

        self.data[key] = value


    def get(
        self,
        key: str,
        default: Any = None,
    ) -> Any:
        """
        Retrieve a value from the shared operation context.
        """

        return self.data.get(key, default)


    def has(
        self,
        key: str,
    ) -> bool:
        """
        Check whether a value exists in the context.
        """

        return key in self.data


    def remove(
        self,
        key: str,
    ) -> Any:
        """
        Remove and return a value from the context.

        Returns None if the key does not exist.
        """

        return self.data.pop(key, None)


    def clear_data(self) -> None:
        """
        Clear operation-specific data stored in the context.
        """

        self.data.clear()


# =====================================================================
# Base Operation
# =====================================================================


class Operation(ABC):
    """
    Base class for every pipeline operation.

    Lifecycle

        prepare()
            ↓
        build_job()
            ↓
        FFmpegRunner executes job
            ↓
        finalize()
    """

    def __init__(
        self,
        name: str | None = None,
    ) -> None:
        self.name = name or self.__class__.__name__

    # -----------------------------------------------------------------

    def prepare(
        self,
        context: OperationContext,
    ) -> None:
        """
        Called before build_job().

        Override when an operation needs to inspect media,
        calculate filters, validate inputs, etc.
        """

    # -----------------------------------------------------------------

    @abstractmethod
    def build_job(
        self,
        context: OperationContext,
    ) -> FFmpegJob | None:
        """
        Build the FFmpeg job for this operation.

        Return None if no FFmpeg execution is required.
        """

        raise NotImplementedError

    # -----------------------------------------------------------------

    def finalize(
        self,
        context: OperationContext,
    ) -> None:
        """
        Called after successful execution.

        By default, the newly generated output becomes the
        input for the next operation.
        """

        context.advance()

    # -----------------------------------------------------------------

    def rollback(
        self,
        context: OperationContext,
        exception: Exception,
    ) -> None:
        """
        Optional cleanup after failure.

        Override if an operation creates temporary files or
        allocates resources that require cleanup.
        """
        

    # -----------------------------------------------------------------

    @property
    def display_name(self) -> str:
        return self.name

    # -----------------------------------------------------------------

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name={self.name!r})"