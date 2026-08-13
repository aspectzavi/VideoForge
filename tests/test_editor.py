"""
VideoForge Editor Smoke Test
"""

from videoforge.editor.editor import Editor
from videoforge.media.asset import MediaAsset
from videoforge.media.clip import Clip
from videoforge.media.timeline import Timeline
from videoforge.media.track import Track


def main() -> None:
    print("=" * 50)
    print("VideoForge Editor Smoke Test")
    print("=" * 50)

    # --------------------------------------------------
    # Load media
    # --------------------------------------------------

    asset = MediaAsset.load("example.mp4")

    clip = Clip(asset=asset)

    # --------------------------------------------------
    # Build timeline
    # --------------------------------------------------

    track = Track(name="Video 1")
    track.add_clip(clip)

    timeline = Timeline()
    timeline.add_track(track)

    # --------------------------------------------------
    # Create editor
    # --------------------------------------------------

    editor = Editor(timeline)

    print("\nInitial Timeline")
    print("----------------")
    print("Tracks   :", editor.timeline.track_count)
    print("Clips    :", editor.timeline.clip_count)
    print("Duration :", f"{editor.timeline.duration:.2f}s")

    # --------------------------------------------------
    # Move
    # --------------------------------------------------

    print("\nMove Clip")
    print("---------")

    editor.move.move_clip(
        clip,
        5.0,
    )

    print("Clip start:", clip.timeline_start)

    # --------------------------------------------------
    # Ripple
    # --------------------------------------------------

    print("\nRipple")
    print("------")

    editor.ripple.ripple(
        5.0,
        2.0,
    )

    print("Clip start:", clip.timeline_start)

    # --------------------------------------------------
    # Trim
    # --------------------------------------------------

    print("\nTrim")
    print("----")

    editor.trim.trim(
        clip,
        0.0,
        10.0,
    )

    print("Clip duration:", clip.duration)

    # --------------------------------------------------
    # Split
    # --------------------------------------------------

    print("\nSplit")
    print("-----")

    second = editor.split.split(
        track,
        clip,
        3.0,
    )

    print("Track clips:", len(track.clips))

    # --------------------------------------------------
    # Clipboard
    # --------------------------------------------------

    print("\nClipboard")
    print("---------")

    editor.clipboard.copy([clip])

    pasted = editor.clipboard.paste()

    print("Clipboard items:", len(pasted))

    # --------------------------------------------------
    # Selection
    # --------------------------------------------------

    print("\nSelection")
    print("---------")

    editor.selection.select(clip)

    print(
        "Selected:",
        len(editor.selection.selected),
    )

    # --------------------------------------------------
    # Delete
    # --------------------------------------------------

    print("\nDelete")
    print("------")

    editor.delete.delete_clip(
        track,
        second,
    )

    print("Remaining clips:", len(track.clips))

    # --------------------------------------------------
    # History
    # --------------------------------------------------

    print("\nHistory")
    print("-------")

    print("Undo available:", editor.history.can_undo)
    print("Redo available:", editor.history.can_redo)

    print("\nSUCCESS ✓")


if __name__ == "__main__":
    main()
