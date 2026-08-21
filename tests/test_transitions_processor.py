"""
Fast, pytest-based tests for TransitionProcessor (renderer/transitions.py).

TransitionProcessor.insert_transition() expects a duck-typed object
with .type/.duration/.clip_a/.clip_b (clip_a/clip_b themselves needing
an .id), which is NOT what media/transition.py's real Transition model
provides (confirmed - Transition has no clip_a/clip_b fields at all).
These tests exercise the actual current graph-rewiring logic using
lightweight dummy objects matching what the code really expects, and
one test documents the real-Transition mismatch explicitly rather than
silently working around it.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pytest

from videoforge.media.asset import MediaAsset
from videoforge.media.timeline import Timeline
from videoforge.media.transition import Transition, TransitionType
from videoforge.renderer.graph import GraphNode, RenderGraph
from videoforge.renderer.transitions import TransitionProcessor

SAMPLE_MEDIA = Path("tests/sample_media/input.mp4")


@dataclass
class _DummyTransition:
    """Matches what insert_transition() actually reads off a transition object."""

    type: str
    duration: float
    clip_a: object
    clip_b: object


@pytest.fixture
def asset() -> MediaAsset:
    return MediaAsset.load(SAMPLE_MEDIA)


def test_module_is_importable() -> None:
    """
    Regression test: this file was previously named "transitions,py"
    (a comma, not a period), which meant TransitionProcessor was
    completely unreachable via any normal import -
    ModuleNotFoundError: No module named 'videoforge.renderer.transitions'.
    Renamed to transitions.py; this test simply confirms the module
    now imports (the surrounding imports at the top of this file would
    already fail collection if it didn't, but this makes the intent
    explicit).
    """
    from videoforge.renderer.transitions import TransitionProcessor

    assert TransitionProcessor is not None


def test_apply_with_no_transitions_returns_graph_unchanged() -> None:
    timeline = Timeline()
    graph = RenderGraph()
    graph.add(GraphNode(name="input"))

    result = TransitionProcessor().apply(graph, timeline)

    assert result is graph
    assert len(graph) == 1


def test_insert_transition_rewires_clip_a_to_clip_b() -> None:
    processor = TransitionProcessor()
    graph = RenderGraph()

    node_a = graph.add(GraphNode(name="clip", params={"clip_id": "a"}))
    node_b = graph.add(GraphNode(name="clip", params={"clip_id": "b"}))
    node_a.connect(node_b)

    transition = _DummyTransition(
        type="crossfade",
        duration=1.0,
        clip_a=type("C", (), {"id": "a"})(),
        clip_b=type("C", (), {"id": "b"})(),
    )

    transition_node = processor.insert_transition(graph, transition)

    # original direct edge is removed...
    assert node_b not in node_a.outputs
    assert node_a not in node_b.inputs

    # ...replaced by clip_a -> transition -> clip_b
    assert transition_node in node_a.outputs
    assert node_a in transition_node.inputs
    assert node_b in transition_node.outputs
    assert transition_node in node_b.inputs

    assert transition_node.params["type"] == "crossfade"
    assert transition_node.params["duration"] == 1.0


def test_insert_transition_requires_clip_a_and_clip_b() -> None:
    processor = TransitionProcessor()
    graph = RenderGraph()

    transition = _DummyTransition(type="fade", duration=1.0, clip_a=None, clip_b=None)

    with pytest.raises(ValueError, match="requires clip_a and clip_b"):
        processor.insert_transition(graph, transition)


def test_insert_transition_raises_when_clip_nodes_not_in_graph() -> None:
    processor = TransitionProcessor()
    graph = RenderGraph()  # empty - neither clip node exists

    transition = _DummyTransition(
        type="fade",
        duration=1.0,
        clip_a=type("C", (), {"id": "a"})(),
        clip_b=type("C", (), {"id": "b"})(),
    )

    with pytest.raises(RuntimeError, match="not found in graph"):
        processor.insert_transition(graph, transition)


def test_apply_processes_every_transition_in_the_timeline() -> None:
    timeline = Timeline()
    timeline.transitions = [
        _DummyTransition(
            type="fade",
            duration=1.0,
            clip_a=type("C", (), {"id": "a"})(),
            clip_b=type("C", (), {"id": "b"})(),
        )
    ]

    graph = RenderGraph()
    node_a = graph.add(GraphNode(name="clip", params={"clip_id": "a"}))
    node_b = graph.add(GraphNode(name="clip", params={"clip_id": "b"}))
    node_a.connect(node_b)

    TransitionProcessor().apply(graph, timeline)

    assert len(graph) == 3  # clip_a, clip_b, and the new transition node


def test_insert_transition_does_not_work_with_real_transition_model(
    asset: MediaAsset,
) -> None:
    """
    Documents a genuine, unresolved interface mismatch rather than a
    bug fixed here: media/transition.py's real Transition (used by
    Timeline.transitions and Clip.transition_in/transition_out
    throughout the already-tested media/ and editor/ subsystems) has
    no clip_a/clip_b fields at all - it's a flat descriptor
    (type/duration/offset/easing/parameters). TransitionProcessor
    therefore cannot currently process a real Timeline's transitions;
    it only works with the clip_a/clip_b-shaped duck type used
    elsewhere in this file.

    This is a real architecture question (should Transition gain
    clip references, or should TransitionProcessor instead derive
    clip_a/clip_b by walking each Track's clips and their existing
    transition_in/transition_out fields?) rather than something to
    invent unilaterally, so it's left as a documented gap.
    """
    transition = Transition(type=TransitionType.CROSSFADE, duration=1.0)

    assert not hasattr(transition, "clip_a")
    assert not hasattr(transition, "clip_b")

    processor = TransitionProcessor()
    graph = RenderGraph()

    with pytest.raises(ValueError, match="requires clip_a and clip_b"):
        processor.insert_transition(graph, transition)


def test_find_clip_node_matches_by_clip_id_param() -> None:
    graph = RenderGraph()
    clip_node = graph.add(GraphNode(name="clip", params={"clip_id": "target"}))
    graph.add(GraphNode(name="clip", params={"clip_id": "other"}))
    graph.add(GraphNode(name="scale", params={"filter": "scale=100:100"}))

    found = TransitionProcessor()._find_clip_node(graph, "target")

    assert found is clip_node
    assert TransitionProcessor()._find_clip_node(graph, "missing") is None


def test_find_clip_node_matches_audio_clip_nodes_too() -> None:
    graph = RenderGraph()
    audio_node = graph.add(
        GraphNode(name="audio_clip", params={"clip_id": "audio-1"})
    )

    found = TransitionProcessor()._find_clip_node(graph, "audio-1")

    assert found is audio_node
