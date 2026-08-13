"""
Render Graph

A lightweight directed acyclic graph (DAG) describing the rendering
pipeline before it is compiled into an FFmpeg filter_complex graph.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from uuid import uuid4

# ==========================================================
# Graph Node
# ==========================================================


@dataclass(slots=True)
class GraphNode:
    """
    Represents a render operation.

    Examples
    --------
    Input
    Scale
    Crop
    Overlay
    Transition
    AudioMix
    Subtitle
    Output
    """

    name: str

    params: dict[str, Any] = field(default_factory=dict)

    id: str = field(default_factory=lambda: uuid4().hex[:8])

    inputs: list[GraphNode] = field(default_factory=list)

    outputs: list[GraphNode] = field(default_factory=list)

    # -----------------------------------------------------

    def connect(
        self,
        node: GraphNode,
    ) -> GraphNode:
        """
        Connect this node to another node.
        """

        if node not in self.outputs:
            self.outputs.append(node)

        if self not in node.inputs:
            node.inputs.append(self)

        return node

    # -----------------------------------------------------

    @property
    def is_source(self) -> bool:

        return not self.inputs

    # -----------------------------------------------------

    @property
    def is_sink(self) -> bool:

        return not self.outputs

    # -----------------------------------------------------

    def __repr__(self) -> str:

        return f"GraphNode({self.name}, id={self.id})"


# ==========================================================
# Render Graph
# ==========================================================


class RenderGraph:
    """
    DAG describing the render pipeline.
    """

    def __init__(self) -> None:

        self.nodes: list[GraphNode] = []

    # -----------------------------------------------------

    def add(
        self,
        node: GraphNode,
    ) -> GraphNode:

        self.nodes.append(node)

        return node

    # -----------------------------------------------------

    def connect(
        self,
        source: GraphNode,
        destination: GraphNode,
    ) -> None:

        source.connect(destination)

    # -----------------------------------------------------

    @property
    def sources(self) -> list[GraphNode]:

        return [node for node in self.nodes if node.is_source]

    # -----------------------------------------------------

    @property
    def sinks(self) -> list[GraphNode]:

        return [node for node in self.nodes if node.is_sink]

    # -----------------------------------------------------

    def find(
        self,
        node_id: str,
    ) -> GraphNode | None:

        for node in self.nodes:
            if node.id == node_id:
                return node

        return None

    # -----------------------------------------------------

    def clear(self) -> None:

        self.nodes.clear()

    # -----------------------------------------------------

    def topological_sort(
        self,
    ) -> list[GraphNode]:
        """
        Return nodes in dependency order using Kahn's algorithm.
        """

        incoming = {node: len(node.inputs) for node in self.nodes}

        ready = [node for node in self.nodes if incoming[node] == 0]

        ordered: list[GraphNode] = []

        while ready:
            node = ready.pop(0)

            ordered.append(node)

            for child in node.outputs:
                incoming[child] -= 1

                if incoming[child] == 0:
                    ready.append(child)

        if len(ordered) != len(self.nodes):
            raise RuntimeError("Render graph contains a cycle.")

        return ordered

    # -----------------------------------------------------

    def __len__(self) -> int:

        return len(self.nodes)

    # -----------------------------------------------------

    def __iter__(self):

        return iter(self.nodes)

    # -----------------------------------------------------

    def __repr__(self) -> str:

        return f"RenderGraph(nodes={len(self.nodes)})"
