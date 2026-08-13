from videoforge.media.asset import MediaAsset

asset = MediaAsset.load("tests/sample_media/input.mp4")

print(asset)

print(asset.asset_type)
print(asset.duration)
print(asset.width)
print(asset.height)
print(asset.fps)
print(asset.resolution)
print(asset.has_audio)
print(asset.is_vertical)

print()

print(asset.model_dump())
