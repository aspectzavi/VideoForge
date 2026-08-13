from pathlib import Path

from videoforge.ffmpeg.command import FFmpegCommandBuilder
from videoforge.ffmpeg.job import FFmpegJob

job = FFmpegJob(
    inputs=[Path("input.mp4")],
    output=Path("output.mp4"),
    video_codec="libx264",
    audio_codec="aac",
)

print(FFmpegCommandBuilder.build(job))
