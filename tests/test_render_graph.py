"""
Fast, pytest-based tests for RenderGraph/GraphNode (renderer/graph.py).
"""

from __future__ import annotations

import pytest

from videoforge.renderer.graph import GraphNode, RenderGraph


def test_graph_node_is_hashable() -> None:
    """
    Regression test: GraphNode was a @dataclass(slots=True) with the
    default auto-generated __eq__ and no frozen=True/unsafe_hash=True,
    which makes a dataclass unhashable. RenderGraph.topological_sort()
    uses nodes as dict keys, so every call raised
    TypeError: unhashable type: 'GraphNode'. Fixed with eq=False
    (identity-based equality/hash, appropriate for a mutable node).
    """
    node = GraphNode(name="input")
    hash(node)  # would raise TypeError before the fix
    {node: 1}  # would also raise before the fix


def test_connect_wires_inputs_and_outputs() -> None:
    a = GraphNode(name="a")
    b = GraphNode(name="b")

    a.connect(b)

    assert b in a.outputs
    assert a in b.inputs


def test_add_appends_and_returns_node() -> None:
    graph = RenderGraph()
    node = graph.add(GraphNode(name="input"))

    assert node in graph.nodes
    assert len(graph) == 1


def test_iteration_over_graph() -> None:
    graph = RenderGraph()
    a = graph.add(GraphNode(name="a"))
    b = graph.add(GraphNode(name="b"))

    assert list(graph) == [a, b]


def test_topological_sort_orders_by_dependency() -> None:
    graph = RenderGraph()
    a = graph.add(GraphNode(name="a"))
    b = graph.add(GraphNode(name="b"))
    c = graph.add(GraphNode(name="c"))

    a.connect(b)
    b.connect(c)

    assert graph.topological_sort() == [a, b, c]


def test_topological_sort_handles_diamond_dependency() -> None:
    graph = RenderGraph()
    a = graph.add(GraphNode(name="a"))
    b = graph.add(GraphNode(name="b"))
    c = graph.add(GraphNode(name="c"))
    d = graph.add(GraphNode(name="d"))

    a.connect(b)
    a.connect(c)
    b.connect(d)
    c.connect(d)

    order = graph.topological_sort()

    assert order[0] is a
    assert order[-1] is d
    assert set(order) == {a, b, c, d}


def test_topological_sort_raises_on_cycle() -> None:
    graph = RenderGraph()
    a = graph.add(GraphNode(name="a"))
    b = graph.add(GraphNode(name="b"))

    a.connect(b)
    b.connect(a)  # cycle

    with pytest.raises(RuntimeError, match="cycle"):
        graph.topological_sort()


def test_sources_and_sinks() -> None:
    graph = RenderGraph()
    a = graph.add(GraphNode(name="a"))
    b = graph.add(GraphNode(name="b"))
    c = graph.add(GraphNode(name="c"))

    a.connect(b)
    b.connect(c)

    assert graph.sources == [a]
    assert graph.sinks == [c]


def test_is_source_and_is_sink() -> None:
    a = GraphNode(name="a")
    b = GraphNode(name="b")
    a.connect(b)

    assert a.is_source is True
    assert a.is_sink is False
    assert b.is_source is False
    assert b.is_sink is True


def test_find_by_id() -> None:
    graph = RenderGraph()
    node = graph.add(GraphNode(name="a"))

    assert graph.find(node.id) is node
    assert graph.find("missing") is None


def test_clear() -> None:
    graph = RenderGraph()
    graph.add(GraphNode(name="a"))

    graph.clear()

    assert len(graph) == 0


def test_connect_is_idempotent() -> None:
    a = GraphNode(name="a")
    b = GraphNode(name="b")

    a.connect(b)
    a.connect(b)  # calling again should not duplicate the edge

    assert a.outputs == [b]
    assert b.inputs == [a]
