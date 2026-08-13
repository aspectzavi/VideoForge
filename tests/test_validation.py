from pathlib import Path

from videoforge.ffmpeg.job import FFmpegJob
from videoforge.ffmpeg.validation import JobValidator

job = FFmpegJob(
    inputs=[Path("tests/sample_media/input.mp4")],
    output=Path("output/test.mp4"),
    copy_video=True,
    copy_audio=True,
)

JobValidator.validate(job)

print("Validation passed.")
