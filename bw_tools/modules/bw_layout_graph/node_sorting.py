from typing import List

from .alignment_behavior import NodeAlignmentBehavior, StaticAlignment
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
    offset = get_offset_value(node, node.closest_output_node_in_x)

    node.set_position(
        node.closest_output_node_in_x.pos.x - offset,
        node.farthest_output_nodes[0].pos.y,
    )

    if node not in already_processed:
        behavior = calculate_behavior()
        node.alignment_behavior = behavior
        already_processed.append(node)

    node.alignment_behavior.setup(output_node)


def get_offset_value(node: LayoutNode, output_node: LayoutNode) -> float:
    if node.is_root:
        spacer = SPACER  # * 4
    else:
        spacer = SPACER
    half_output = output_node.width / 2
    half_input = node.width / 2
    return half_output + spacer + half_input


def calculate_behavior() -> NodeAlignmentBehavior:
    return StaticAlignment()
