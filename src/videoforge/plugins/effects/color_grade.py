"""
Example effects plugin: color grading.

Demonstrates a real Plugin delegating to an existing Operation/
Pipeline rather than reimplementing FFmpeg logic itself - this is the
intended pattern for plugins that need FFmpeg processing.
"""

from __future__ import annotations

from pathlib import Path

from videoforge.ffmpeg.pipeline import Pipeline
from videoforge.operations.video.colors import ColorOperation
from videoforge.plugins.base import Plugin


class ColorGradePlugin(Plugin):
    """
    Apply a brightness/contrast/saturation/gamma color grade to a
    video file.
    """

    name = "color_grade"
    version = "0.1.0"
    description = "Apply a color grade (brightness/contrast/saturation/gamma)."
    category = "effects"

    def execute(
        self,
        input_file: str | Path,
        *,
        brightness: float = 0.0,
        contrast: float = 1.0,
        saturation: float = 1.0,
        gamma: float = 1.0,
    ) -> Path:
        operation = ColorOperation(
            brightness=brightness,
            contrast=contrast,
            saturation=saturation,
            gamma=gamma,
        )

        result = Pipeline().add(operation).run(input_file)

        if not result.success:
            raise RuntimeError(
                "Color grade pipeline did not complete successfully."
            )

        return result.context.input_file
