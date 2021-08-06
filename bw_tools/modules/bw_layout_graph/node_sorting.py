from typing import List

from .alignment_behavior import StaticAlignment
from .layout_node import LayoutNode

SPACER = 32


def run_sort(node: LayoutNode):
    position_nodes(node)
    build_alignment_behaviors(node)


def position_nodes(node: LayoutNode):
    for input_node in node.input_nodes:
        node.set_position(
            node.closest_output_node_in_x.pos.x
            - get_offset_value(node, node.closest_output_node_in_x),
            node.farthest_output_nodes_in_x[0].pos.y,
        )
        position_nodes(input_node)


def build_alignment_behaviors(node: LayoutNode):
    for input_node in node.input_nodes:
        if node.alignment_behavior is None:
            node.alignment_behavior = StaticAlignment(node)

        if node.pos.x > node.alignment_behavior.offset_node.pos.x:
            node.alignment_behavior.offset_node = node
            node.alignment_behavior.update_offset(node.pos)
        build_alignment_behaviors(input_node)


def get_offset_value(node: LayoutNode, output_node: LayoutNode) -> float:
    if node.has_branching_outputs:
        spacer = SPACER  # * 4
    else:
        spacer = SPACER
    half_output = output_node.width / 2
    half_input = node.width / 2
    return half_output + spacer + half_input
