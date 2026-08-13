from videoforge.ffmpeg.progress import FFmpegProgressParser

parser = FFmpegProgressParser(total_duration=120)

sample = [
    "frame=250",
    "fps=59.94",
    "bitrate=1532.0kbits/s",
    "out_time_us=30000000",
    "out_time_ms=30000000",
    "out_time=00:00:30.000000",
    "speed=2.10x",
    "progress=continue",
]

progress = None

for item in parser.parse(sample):
    progress = item

if progress is None:
    raise RuntimeError("No progress information parsed.")

print(progress.model_dump())
print(f"Percentage: {progress.percentage}%")
print(f"Elapsed: {progress.elapsed_seconds:.2f}s")
