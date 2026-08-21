"""
Fast, pytest-based tests for RenderGraphBuilder (renderer/builder.py).
"""

from __future__ import annotations

from videoforge.renderer.builder import RenderGraphBuilder
from videoforge.renderer.graph import GraphNode, RenderGraph


def test_build_empty_graph_returns_empty_filter_complex() -> None:
    graph = RenderGraph()
    result = RenderGraphBuilder().build(graph)

    assert result.filter_complex == ""


def test_build_input_output_only() -> None:
    graph = RenderGraph()
    inp = graph.add(GraphNode(name="input"))
    out = graph.add(GraphNode(name="output"))
    inp.connect(out)

    result = RenderGraphBuilder().build(graph)

    assert result.filter_complex == ""
    assert result.video_output == "[0:v]"


def test_build_single_filter_chain() -> None:
    graph = RenderGraph()
    inp = graph.add(GraphNode(name="input"))
    scale = graph.add(GraphNode(name="scale", params={"filter": "scale=1280:720"}))
    out = graph.add(GraphNode(name="output"))

    inp.connect(scale)
    scale.connect(out)

    result = RenderGraphBuilder().build(graph)

    assert result.filter_complex == "[0:v]scale=1280:720[v0]"
    assert result.video_output == "[v0]"


def test_build_multiple_filters_chain_labels_sequentially() -> None:
    graph = RenderGraph()
    inp = graph.add(GraphNode(name="input"))
    scale = graph.add(GraphNode(name="scale", params={"filter": "scale=1280:720"}))
    crop = graph.add(GraphNode(name="crop", params={"filter": "crop=1280:720:0:0"}))
    out = graph.add(GraphNode(name="output"))

    inp.connect(scale)
    scale.connect(crop)
    crop.connect(out)

    result = RenderGraphBuilder().build(graph)

    assert result.filter_complex == (
        "[0:v]scale=1280:720[v0];[v0]crop=1280:720:0:0[v1]"
    )
    assert result.video_output == "[v1]"


def test_build_skips_nodes_without_a_filter_param() -> None:
    graph = RenderGraph()
    inp = graph.add(GraphNode(name="input"))
    marker = graph.add(GraphNode(name="marker"))  # no "filter" param
    out = graph.add(GraphNode(name="output"))

    inp.connect(marker)
    marker.connect(out)

    result = RenderGraphBuilder().build(graph)

    assert result.filter_complex == ""


def test_build_records_stream_labels_for_every_node() -> None:
    graph = RenderGraph()
    inp = graph.add(GraphNode(name="input"))
    scale = graph.add(GraphNode(name="scale", params={"filter": "scale=1280:720"}))
    out = graph.add(GraphNode(name="output"))

    inp.connect(scale)
    scale.connect(out)

    result = RenderGraphBuilder().build(graph)

    assert result.stream_labels[inp.id] == "[0:v]"
    assert result.stream_labels[scale.id] == "[v0]"
    assert result.stream_labels[out.id] == "[v0]"  # output re-uses the last label
