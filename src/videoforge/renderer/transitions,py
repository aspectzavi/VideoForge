"""
Timeline Transition Processing

Applies timeline transitions by inserting transition nodes into the
RenderGraph before it is compiled into an FFmpeg filter graph.

This module is intentionally renderer-agnostic. It knows nothing about
FFmpeg syntax—it only manipulates the RenderGraph.
"""

from __future__ import annotations

from videoforge.media.timeline import Timeline
from videoforge.renderer.graph import GraphNode
from videoforge.renderer.graph import RenderGraph


class TransitionProcessor:
    """
    Inserts transition nodes into a RenderGraph.

    Supported (current)
    -------------------
    ✓ Crossfade
    ✓ Fade
    ✓ Dissolve

    Planned
    -------
    - Wipe
    - Slide
    - Zoom
    - Push
    - Iris
    - Blur
    - Luma
    - Custom shader transitions
    """

    # ---------------------------------------------------------

    def apply(
        self,
        graph: RenderGraph,
        timeline: Timeline,
    ) -> RenderGraph:
        """
        Apply every transition contained in the timeline.
        """

        if not getattr(timeline, "transitions", None):
            return graph

        for transition in timeline.transitions:

            self.insert_transition(
                graph,
                transition,
            )

        return graph

    # ---------------------------------------------------------

    def insert_transition(
        self,
        graph: RenderGraph,
        transition,
    ) -> GraphNode:
        """
        Insert a transition node.

        Expected transition object fields:

            type
            duration
            clip_a
            clip_b
        """

        clip_a = getattr(
            transition,
            "clip_a",
            None,
        )

        clip_b = getattr(
            transition,
            "clip_b",
            None,
        )

        if clip_a is None or clip_b is None:
            raise ValueError(
                "Transition requires clip_a and clip_b."
            )

        node_a = self._find_clip_node(
            graph,
            clip_a.id,
        )

        node_b = self._find_clip_node(
            graph,
            clip_b.id,
        )

        if node_a is None or node_b is None:
            raise RuntimeError(
                "Transition clips not found in graph."
            )

        transition_node = graph.add(
            GraphNode(
                name="transition",
                params={
                    "type": transition.type,
                    "duration": transition.duration,
                    "clip_a": clip_a.id,
                    "clip_b": clip_b.id,
                },
            )
        )

        #
        # Rewire:
        #
        # clip_a ----> clip_b
        #
        # becomes
        #
        # clip_a -> transition -> clip_b
        #

        if node_b in node_a.outputs:
            node_a.outputs.remove(node_b)

        if node_a in node_b.inputs:
            node_b.inputs.remove(node_a)

        node_a.connect(transition_node)

        transition_node.connect(node_b)

        return transition_node

    # ---------------------------------------------------------

    def _find_clip_node(
        self,
        graph: RenderGraph,
        clip_id: str,
    ) -> GraphNode | None:

        for node in graph:

            if node.name not in (
                "clip",
                "audio_clip",
            ):
                continue

            if (
                node.params.get("clip_id")
                == clip_id
            ):
                return node

        return None