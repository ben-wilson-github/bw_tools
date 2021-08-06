from typing import List

from .alignment_behavior import StaticAlignment
from .layout_node import LayoutNode

SPACER = 32


def run_sort(node: LayoutNode, already_processed: List[LayoutNode]):
    for input_node in node.input_nodes:
        process_node(input_node, node, already_processed)
        run_sort(input_node, already_processed)


def process_node(
    node: LayoutNode,
    output_node: LayoutNode,
    already_processed: List[LayoutNode],
):
    node.set_position(
        node.closest_output_node_in_x.pos.x
        - get_offset_value(node, node.closest_output_node_in_x),
        node.farthest_output_nodes_in_x[0].pos.y,
    )

    if node not in already_processed:
        node.alignment_behavior = StaticAlignment(node)
        already_processed.append(node)

    if output_node.pos.x > node.alignment_behavior.offset_node.pos.x:
        node.alignment_behavior.offset_node = output_node
        node.alignment_behavior.update_offset(node.pos)


def get_offset_value(node: LayoutNode, output_node: LayoutNode) -> float:
    if node.has_branching_outputs:
        spacer = SPACER  # * 4
    else:
        spacer = SPACER
    half_output = output_node.width / 2
    half_input = node.width / 2
    return half_output + spacer + half_input
