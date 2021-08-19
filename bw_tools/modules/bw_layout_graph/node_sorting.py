from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .bw_layout_graph import LayoutSettings

from .alignment_behavior import StaticAlignment
from .layout_node import LayoutNode


@dataclass
class NodeSorter:
    settings: LayoutSettings

    def position_nodes(self, output_node: LayoutNode):
        input_node: LayoutNode
        for input_node in output_node.input_nodes:
            input_node.set_position(
                input_node.closest_output_node_in_x.pos.x
                - self.get_offset_value(
                    input_node, input_node.closest_output_node_in_x
                ),
                input_node.farthest_output_nodes_in_x[0].pos.y,
            )
            self.position_nodes(input_node)

    def build_alignment_behaviors(self, output_node: LayoutNode):
        input_node: LayoutNode
        for input_node in output_node.input_nodes:
            if input_node.alignment_behavior is None:
                input_node.alignment_behavior = StaticAlignment(input_node)

            if (
                output_node.pos.x
                > input_node.alignment_behavior.offset_node.pos.x
            ):
                input_node.alignment_behavior.offset_node = output_node
                input_node.alignment_behavior.update_offset(input_node.pos)
            self.build_alignment_behaviors(input_node)

    def get_offset_value(
        self, node: LayoutNode, output_node: LayoutNode
    ) -> float:
        half_output = output_node.width / 2
        half_input = node.width / 2
        return half_output + self.settings.node_spacing + half_input
