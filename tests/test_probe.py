from pathlib import Path

from videoforge.ffmpeg.probe import probe

media = probe.probe(Path("tests/sample_media/input.mp4"))

print()

print(media.model_dump_json(indent=4))
