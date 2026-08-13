from pathlib import Path

import pytest

from videoforge.ffmpeg.pipeline import Pipeline, PipelineResult
from videoforge.operations.base import Operation, OperationContext


class PipelineTestOperation(Operation):
    """
    Minimal operation used to test Pipeline orchestration
    without actually running FFmpeg.
    """

    name = "Test Operation"

    def prepare(self, context: OperationContext) -> None:
        context.set("prepared", True)

    def build_job(self, context: OperationContext):
        return None

    def finalize(self, context: OperationContext) -> None:
        context.set("finalized", True)


class SecondTestOperation(Operation):
    """
    Second operation used to verify that context is shared
    between pipeline operations.
    """

    name = "Second Operation"

    def prepare(self, context: OperationContext) -> None:
        assert context.get("prepared") is True
        context.set("second_prepared", True)

    def build_job(self, context: OperationContext):
        return None

    def finalize(self, context: OperationContext) -> None:
        context.set("second_finalized", True)


def test_pipeline_can_be_created() -> None:
    pipeline = Pipeline()

    assert pipeline.operations == []


def test_pipeline_add_returns_pipeline() -> None:
    pipeline = Pipeline()
    operation = PipelineTestOperation()

    result = pipeline.add(operation)

    assert result is pipeline
    assert pipeline.operations == [operation]


def test_pipeline_clear() -> None:
    pipeline = Pipeline()

    pipeline.add(PipelineTestOperation())
    pipeline.add(SecondTestOperation())

    assert len(pipeline.operations) == 2

    pipeline.clear()

    assert pipeline.operations == []


def test_pipeline_runs_operations_without_ffmpeg() -> None:
    pipeline = Pipeline()
    pipeline.add(PipelineTestOperation())

    result = pipeline.run(
        Path("tests/sample_media/input.mp4")
    )

    assert isinstance(result, PipelineResult)
    assert result.success is True
    assert result.elapsed >= 0

    assert result.context.get("prepared") is True
    assert result.context.get("finalized") is True


def test_pipeline_shares_context_between_operations() -> None:
    pipeline = Pipeline()

    pipeline.add(PipelineTestOperation())
    pipeline.add(SecondTestOperation())

    result = pipeline.run(
        Path("tests/sample_media/input.mp4")
    )

    assert result.success is True

    assert result.context.get("prepared") is True
    assert result.context.get("finalized") is True
    assert result.context.get("second_prepared") is True
    assert result.context.get("second_finalized") is True


def test_pipeline_context_contains_input_file() -> None:
    input_file = Path("tests/sample_media/input.mp4")

    pipeline = Pipeline()
    pipeline.add(PipelineTestOperation())

    result = pipeline.run(input_file)

    assert result.context.input_file == input_file


def test_pipeline_context_contains_total_steps() -> None:
    pipeline = Pipeline()

    pipeline.add(PipelineTestOperation())
    pipeline.add(SecondTestOperation())

    result = pipeline.run(
        Path("tests/sample_media/input.mp4")
    )

    assert result.context.total_steps == 2


def test_empty_pipeline_succeeds() -> None:
    pipeline = Pipeline()

    result = pipeline.run(
        Path("tests/sample_media/input.mp4")
    )

    assert result.success is True
    assert result.context.total_steps == 0
    assert result.elapsed >= 0


def test_pipeline_operation_failure_propagates() -> None:
    class FailingOperation(Operation):
        name = "Failing Operation"

        def prepare(self, context: OperationContext) -> None:
            raise RuntimeError("intentional pipeline failure")

        def build_job(self, context: OperationContext):
            return None

        def finalize(self, context: OperationContext) -> None:
            pass

    pipeline = Pipeline()
    pipeline.add(FailingOperation())

    with pytest.raises(RuntimeError, match="intentional pipeline failure"):
        pipeline.run(
            Path("tests/sample_media/input.mp4")
        )