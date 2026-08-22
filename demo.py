"""
VideoForge - Feature Demo / Usage Guide
=========================================

Run this any time you want to sanity-check the engine or see how the
current pieces fit together:

    python demo.py

Each section below is self-contained and demonstrates a REAL, verified
-working part of the engine (as of the last full test run - see
memory/commit history for exactly what's been tested). Nothing here
is aspirational; every call in this file actually runs.

Sections:
    1. Media assets       - loading and probing a video file
    2. Timeline model      - building tracks and clips
    3. Editor + undo/redo  - non-destructive editing operations
    4. Real FFmpeg pipeline - actually processing video with FFmpeg
    5. Plugin system        - running a plugin through the registry
    6. Media library        - organizing assets, bins, collections

Output files land in ./demo_output/ (gitignored) so re-running this
never pollutes the repo.

See the "WHAT'S NOT WIRED UP YET" section at the very bottom for a
running list of real capabilities that exist in the codebase but
aren't safe to demo here (either unwired, or documented gaps).
"""

from __future__ import annotations

from pathlib import Path

SAMPLE_MEDIA = Path("tests/sample_media/input.mp4")
OUTPUT_DIR = Path("demo_output")


def section(title: str) -> None:
    print()
    print("=" * 70)
    print(title)
    print("=" * 70)


# ---------------------------------------------------------------------
# 1. Media assets
# ---------------------------------------------------------------------


def demo_media_asset() -> None:
    section("1. Media Assets - load and probe a video file")

    from videoforge.media.asset import MediaAsset

    asset = MediaAsset.load(SAMPLE_MEDIA)
    print(f"Loaded: {asset.filename}")
    print(f"  Type: {asset.asset_type}")
    print(f"  Duration: {asset.duration:.2f}s")
    print(f"  Resolution: {asset.width}x{asset.height}")
    print(f"  FPS: {asset.fps:.2f}")
    print(f"  Has audio: {asset.has_audio}")

    # Tagging / rating / favoriting
    asset.add_tag("demo")
    asset.set_rating(5)
    asset.favorite_asset()
    print(f"  Tags: {asset.tags}, Rating: {asset.rating}, Favorite: {asset.favorite}")


# ---------------------------------------------------------------------
# 2. Timeline model
# ---------------------------------------------------------------------


def demo_timeline() -> "Timeline":
    section("2. Timeline Model - tracks and clips")

    from videoforge.media.asset import MediaAsset
    from videoforge.media.clip import Clip
    from videoforge.media.timeline import Timeline
    from videoforge.media.track import Track

    asset = MediaAsset.load(SAMPLE_MEDIA)

    track = Track(name="V1")

    clip_a = Clip(asset=asset)
    clip_a.trim(0, 5)  # use seconds 0-5 of the source
    clip_a.move(0)  # place at timeline position 0
    track.add_clip(clip_a)

    clip_b = Clip(asset=asset)
    clip_b.trim(10, 15)  # use seconds 10-15 of the source
    clip_b.move(5)  # place right after clip_a
    track.add_clip(clip_b)

    timeline = Timeline()
    timeline.add_track(track)

    print(f"Track has {track.clip_count} clips")
    print(f"Timeline duration: {timeline.duration:.2f}s")
    for clip in track.clips:
        print(
            f"  Clip {clip.id[:8]}: timeline "
            f"{clip.timeline_start:.1f}-{clip.timeline_end:.1f}s "
            f"(source {clip.source_start:.1f}-{clip.source_end:.1f}s)"
        )

    return timeline


# ---------------------------------------------------------------------
# 3. Editor + undo/redo
# ---------------------------------------------------------------------


def demo_editor() -> None:
    section("3. Editor - non-destructive editing with undo/redo")

    from videoforge.editor.editor import Editor
    from videoforge.media.asset import MediaAsset
    from videoforge.media.clip import Clip
    from videoforge.media.timeline import Timeline
    from videoforge.media.track import Track

    asset = MediaAsset.load(SAMPLE_MEDIA)
    track = Track(name="V1")
    clip = Clip(asset=asset)
    clip.trim(0, 10)
    track.add_clip(clip)

    timeline = Timeline()
    timeline.add_track(track)

    editor = Editor(timeline)

    print(f"Clip starts at: {clip.timeline_start}s")

    editor.move_clip(track, clip, 20.0)
    print(f"After move_clip(20.0): {clip.timeline_start}s")

    editor.history.undo()
    print(f"After undo(): {clip.timeline_start}s")

    editor.history.redo()
    print(f"After redo(): {clip.timeline_start}s")

    # Split, then undo - restores the exact original clip object
    left, right = editor.split_clip(track, clip, 25.0)
    print(f"After split at 25.0s: {track.clip_count} clips")

    editor.history.undo()
    print(f"After undo(): {track.clip_count} clip(s), same object: {track.clips[0] is clip}")


# ---------------------------------------------------------------------
# 4. Real FFmpeg pipeline
# ---------------------------------------------------------------------


def demo_pipeline() -> None:
    section("4. Real FFmpeg Pipeline - actually processing video")

    from videoforge.ffmpeg.pipeline import Pipeline
    from videoforge.operations.video.trim import TrimOperation
    from videoforge.operations.video.colors import ColorOperation
    from videoforge.operations.export.thumbnail import ThumbnailOperation

    print("Running: trim to 3s -> color grade -> extract thumbnail")
    print("(this actually invokes FFmpeg and takes a few seconds)")

    thumbnail_path = OUTPUT_DIR / "demo_thumbnail.jpg"

    pipeline = (
        Pipeline()
        .add(TrimOperation(0.0, 3.0))
        .add(ColorOperation(brightness=0.05, contrast=1.1, saturation=1.2))
        .add(ThumbnailOperation(thumbnail_path, time=1.0, width=320))
    )

    result = pipeline.run(SAMPLE_MEDIA)

    print(f"Success: {result.success}")
    print(f"Elapsed: {result.elapsed:.2f}s")
    print(f"Processed video: {result.context.input_file}")
    print(f"Thumbnail: {thumbnail_path} (exists: {thumbnail_path.exists()})")


# ---------------------------------------------------------------------
# 5. Plugin system
# ---------------------------------------------------------------------


def demo_plugins() -> None:
    section("5. Plugin System - running a plugin through the registry")

    from videoforge.ffmpeg.pipeline import Pipeline
    from videoforge.operations.video.trim import TrimOperation
    from videoforge.plugins.effects.color_grade import ColorGradePlugin
    from videoforge.plugins.registry import PluginRegistry

    # First, produce a short real clip to run the plugin on.
    trimmed = Pipeline().add(TrimOperation(0.0, 2.0)).run(SAMPLE_MEDIA)
    short_clip = trimmed.context.input_file

    registry = PluginRegistry()
    registry.register(ColorGradePlugin())

    print(f"Registered plugins: {[p.name for p in registry.list_plugins()]}")

    output = registry.execute(
        "color_grade",
        short_clip,
        brightness=0.1,
        contrast=1.15,
        saturation=1.3,
    )

    print(f"Plugin output: {output} (exists: {output.exists()})")

    registry.unregister("color_grade")
    print(f"After unregister: {list(registry.list_plugins())}")


# ---------------------------------------------------------------------
# 6. Media library
# ---------------------------------------------------------------------


def demo_library() -> None:
    section("6. Media Library - organizing assets, bins, collections")

    from videoforge.media.library import MediaLibrary

    library = MediaLibrary()
    asset = library.import_file(SAMPLE_MEDIA)

    footage_bin = library.create_bin("Footage")
    footage_bin.add_asset(asset.id)

    favorites = library.create_collection("Favorites")
    favorites.add_asset(asset.id)

    print(f"Library: {library.asset_count} asset(s), {library.bin_count} bin(s), "
          f"{library.collection_count} collection(s)")
    print(f"Videos: {library.video_count}, Audio: {library.audio_count}")
    print(f"Search 'input': {[a.filename for a in library.search('input')]}")


# ---------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------

WHATS_NOT_WIRED_UP_YET = """
WHAT'S NOT DEMOED HERE (and why)
---------------------------------
- operations/ai/*  - still empty stub files. Real AI features
  (transcription, face tracking, scene detection, silence removal,
  smart crop) need model integration (Whisper/MediaPipe/etc) that
  hasn't been built yet.

- Keyframe/KeyframeTrack (media/keyframe.py) - a real, tested
  animation-curve implementation, but not yet wired into Effect or
  Clip's parameters. Usable standalone today if you want to animate
  a value over time yourself.

- MediaProxy (media/proxy.py) - a fuller, standalone proxy-tracking
  model. Not wired into MediaAsset, which already has its own
  simpler built-in proxy_path/has_proxy fields.

- TransitionProcessor (renderer/transitions.py) - works, but only
  with a duck-typed clip_a/clip_b object shape. The real Transition
  model (media/transition.py) used by Timeline/Clip doesn't carry
  clip references, so this can't process a real Timeline's
  transitions yet - a genuine open design question, not a bug.

- apps/, top-level ai/, assets/, templates/ - entirely empty
  scaffolding, no real code at all yet.

Everything else demoed above is real, tested, and passing in the
full test suite (run `pytest -m "not integration"` for the fast
suite, or add -m integration for the slower real-FFmpeg tests).
"""


def main() -> None:
    OUTPUT_DIR.mkdir(exist_ok=True)

    demo_media_asset()
    demo_timeline()
    demo_editor()
    demo_pipeline()
    demo_plugins()
    demo_library()

    section("Done")
    print(f"Output files are in: {OUTPUT_DIR.resolve()}")
    print(WHATS_NOT_WIRED_UP_YET)


if __name__ == "__main__":
    main()
