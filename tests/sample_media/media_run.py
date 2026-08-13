from pathlib import Path

from videoforge.ffmpeg.job import FFmpegJob
from videoforge.ffmpeg.runner import FFmpegRunner

job = FFmpegJob(
    inputs=[Path("tests/sample_media/input.mp4")],
    output=Path("tests/output/copied.mp4"),
)

FFmpegRunner().run(job)
