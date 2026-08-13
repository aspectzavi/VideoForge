"""
Render Graph Builder

Compiles a RenderGraph into an FFmpeg filter_complex string.

The builder is intentionally independent from the pipeline and renderer.
It only understands graph nodes and produces FFmpeg-compatible filter
descriptions.

Future responsibilities
-----------------------
- Automatic stream labels
- Complex branching
- Overlay chains
- Transition compilation
- Audio graph generation
- Graph optimization
"""

from __future__ import annotations

from dataclasses import dataclass, field

from videoforge.renderer.graph import RenderGraph

# ==========================================================
# Builder Result
# ==========================================================


@dataclass(slots=True)
class BuildResult:
    """
    Output of graph compilation.
    """

    filter_complex: str

    video_output: str | None = None

    audio_output: str | None = None

    stream_labels: dict[str, str] = field(default_factory=dict)


# ==========================================================
# Builder
# ==========================================================


class RenderGraphBuilder:
    """
    Compiles a RenderGraph into FFmpeg filter_complex.

    Current implementation supports simple linear graphs.

    Future versions will support:

    - branching
    - overlays
    - transitions
    - audio mixing
    - subtitles
    - multiple outputs
    """

    def build(
        self,
        graph: RenderGraph,
    ) -> BuildResult:

        ordered = graph.topological_sort()

        if not ordered:
            return BuildResult(filter_complex="")

        lines: list[str] = []

        labels: dict[str, str] = {}

        current_video = "[0:v]"

        video_index = 0

        for node in ordered:
            name = node.name.lower()

            # -----------------------------------------
            # Input node
            # -----------------------------------------

            if name == "input":
                labels[node.id] = current_video

                continue

            # -----------------------------------------
            # Output node
            # -----------------------------------------

            if name == "output":
                labels[node.id] = current_video

                continue

            # -----------------------------------------
            # Generic filter node
            # -----------------------------------------

            expression = node.params.get("filter")

            if not expression:
                continue

            output_label = f"[v{video_index}]"

            lines.append(f"{current_video}{expression}{output_label}")

            current_video = output_label

            labels[node.id] = output_label

            video_index += 1

        return BuildResult(
            filter_complex=";".join(lines),
            video_output=current_video,
            stream_labels=labels,
        )
