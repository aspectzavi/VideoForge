"""
VideoForge Events

These are immutable event models emitted throughout the VideoForge
pipeline. They contain no business logic and are dispatched through
engine.dispatcher.EventDispatcher.
"""

from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel, Field

# =====================================================================
# Base Event
# =====================================================================


class Event(BaseModel):
    """
    Base class for every event.
    """

    event: str = Field(default="event")


# =====================================================================
# Pipeline Events
# =====================================================================


class PipelineStartedEvent(Event):
    event: str = "pipeline.started"

    pipeline: str

    steps: int


class PipelineCompletedEvent(Event):
    event: str = "pipeline.completed"

    elapsed: float


class PipelineCancelledEvent(Event):
    event: str = "pipeline.cancelled"

    reason: str | None = None


class PipelineFailedEvent(Event):
    event: str = "pipeline.failed"

    error: str


# =====================================================================
# Step Events
# =====================================================================


class StepStartedEvent(Event):
    event: str = "step.started"

    index: int

    total: int

    name: str


class StepCompletedEvent(Event):
    event: str = "step.completed"

    index: int

    total: int

    name: str

    elapsed: float


class StepFailedEvent(Event):
    event: str = "step.failed"

    index: int

    total: int

    name: str

    error: str


# =====================================================================
# FFmpeg Progress
# =====================================================================


class ProgressEvent(Event):
    event: str = "ffmpeg.progress"

    percentage: float

    elapsed_seconds: float

    speed: str | None = None

    fps: float | None = None

    frame: int | None = None

    bitrate: str | None = None

    eta_seconds: float | None = None


# =====================================================================
# Media Events
# =====================================================================


class MediaProbedEvent(Event):
    event: str = "media.probed"

    path: Path

    duration: float | None = None

    width: int | None = None

    height: int | None = None

    fps: float | None = None


# =====================================================================
# Job Events
# =====================================================================


class JobCreatedEvent(Event):
    event: str = "job.created"

    operation: str

    output: Path


class JobStartedEvent(Event):
    event: str = "job.started"

    command: list[str]


class JobCompletedEvent(Event):
    event: str = "job.completed"

    output: Path

    elapsed: float


class JobFailedEvent(Event):
    event: str = "job.failed"

    error: str


# =====================================================================
# Operation Events
# =====================================================================


class OperationStartedEvent(Event):
    event: str = "operation.started"

    name: str


class OperationCompletedEvent(Event):
    event: str = "operation.completed"

    name: str

    elapsed: float


class OperationFailedEvent(Event):
    event: str = "operation.failed"

    name: str

    error: str


# =====================================================================
# Asset Events
# =====================================================================


class AssetLoadedEvent(Event):
    event: str = "asset.loaded"

    path: Path


class AssetSavedEvent(Event):
    event: str = "asset.saved"

    path: Path


# =====================================================================
# Plugin Events
# =====================================================================


class PluginLoadedEvent(Event):
    event: str = "plugin.loaded"

    plugin: str


class PluginUnloadedEvent(Event):
    event: str = "plugin.unloaded"

    plugin: str


# =====================================================================
# AI Events
# =====================================================================


class AIStartedEvent(Event):
    event: str = "ai.started"

    model: str


class AICompletedEvent(Event):
    event: str = "ai.completed"

    model: str

    elapsed: float


class AIFailedEvent(Event):
    event: str = "ai.failed"

    model: str

    error: str


# =====================================================================
# Export Events
# =====================================================================


class ExportStartedEvent(Event):
    event: str = "export.started"

    output: Path


class ExportCompletedEvent(Event):
    event: str = "export.completed"

    output: Path

    elapsed: float


class ExportFailedEvent(Event):
    event: str = "export.failed"

    output: Path

    error: str
