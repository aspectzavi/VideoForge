from pathlib import Path

from videoforge.media.asset import MediaAsset
from videoforge.media.clip import Clip
from videoforge.media.timeline import Timeline
from videoforge.media.track import Track

video = Path(__file__).parent.parent / "example.mp4"

asset = MediaAsset.load(video)

clip = Clip(asset=asset)

track = Track(name="Video 1")
track.add_clip(clip)

timeline = Timeline()
timeline.add_track(track)

print("=" * 40)
print("Timeline created successfully")
print("=" * 40)

print(f"Tracks      : {timeline.track_count}")
print(f"Clips       : {timeline.clip_count}")
print(f"Duration    : {timeline.duration:.2f}s")

print()

print("Asset")
print(f"Filename    : {asset.filename}")
print(f"Type        : {asset.asset_type}")
print(f"Exists      : {asset.exists}")
print(f"Resolution  : {asset.resolution}")
print(f"FPS         : {asset.fps}")
print(f"Has Audio   : {asset.has_audio}")

print()

print("Clip")
print(f"Start       : {clip.timeline_start}")
print(f"End         : {clip.timeline_end}")
print(f"Duration    : {clip.duration}")
