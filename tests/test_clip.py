from videoforge.media.asset import MediaAsset
from videoforge.media.clip import Clip

asset = MediaAsset.load("tests/sample_media/input.mp4")

clip = Clip(
    asset=asset,
)

clip.trim(
    10,
    30,
)

clip.move(
    5,
)

clip.set_speed(
    1.5,
)

print(clip)
print()

print("Duration:", clip.duration)
print("Timeline Start:", clip.timeline_start)
print("Timeline End:", clip.timeline_end)
print("Resolution:", clip.resolution)

print()

copy = clip.clone()

print(copy)

print()

print(clip.model_dump())
