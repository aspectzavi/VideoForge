from pathlib import Path

import pytest

from videoforge.ffmpeg.pipeline import Pipeline
from videoforge.operations.video.vertical import VerticalStep


@pytest.mark.integration
def test_vertical_crop(tmp_path: Path) -> None:
    output = tmp_path / "vertical.mp4"

    pipeline = Pipeline().add(
        VerticalStep(
            output=output,
            mode="crop",
        )
    )

    result = pipeline.run(
        "tests/sample_media/input.mp4"
    )

    assert result.success
    assert output.exists()