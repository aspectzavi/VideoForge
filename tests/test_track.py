from videoforge.media.asset import MediaAsset
from videoforge.media.clip import Clip
from videoforge.media.track import Track

asset = MediaAsset.load(
    "tests/sample_media/input.mp4",
)

track = Track(
    name="Video Track 1",
)

clip1 = Clip(asset=asset)
clip1.trim(0, 10)
clip1.move(0)

clip2 = Clip(asset=asset)
clip2.trim(10, 20)
clip2.move(12)

track.add_clip(clip1)
track.add_clip(clip2)

print(track)
print()

print("Duration:", track.duration)
print("Clip Count:", track.clip_count)
print()

for clip in track.iter_clips():
    print(
        clip.timeline_start,
        "->",
        clip.timeline_end,
    )

print()

print(
    "Clip at 5s:",
    track.clip_at(5),
)

print(
    "Clip at 15s:",
    track.clip_at(15),
)

print()

print(
    "Overlaps:",
    track.has_overlap(clip2),
)

track.ripple(
    12,
    5,
)

print()

print("After ripple:")

for clip in track.iter_clips():
    print(
        clip.timeline_start,
        "->",
        clip.timeline_end,
    )
