from typing import List

from common import bw_node
from . import alignment_behavior


SPACER = 32


def run_sort(node: bw_node.Node, already_processed: List[bw_node.Node]):
    for input_node in node.input_nodes:
        process_node(input_node, node, already_processed)
        run_sort(input_node, already_processed)


def get_offset_value(node: bw_node.Node, output_node: bw_node.Node) -> float:
    if node.is_root:
        spacer = SPACER * 4
    else:
        spacer = SPACER
    half_output = output_node.width / 2
    half_input = node.width / 2
    return half_output + spacer + half_input


def calculate_behavior(node: bw_node.Node) -> alignment_behavior.NodeAlignmentBehavior:
    if not node.is_root:
        return alignment_behavior.StaticAlignment()

    # If one of the input nodes has multiple inputs connected,
    # then it is likely to expand later.
    # Make it static
    for output_node in node.output_nodes:
        for input_node in output_node.input_nodes:
            if input_node is node:
                continue
            if input_node.input_node_count > 1:
                return alignment_behavior.StaticAlignment()
    return alignment_behavior.AverageToOutputsYAxis()


def process_node(node: bw_node.Node, output_node: bw_node.Node, already_processed: List[bw_node.Node]):
    offset = get_offset_value(node, node.closest_output_node_in_x)
    node.set_position(node.closest_output_node_in_x.pos.x - offset,
                      node.closest_output_node_in_x.pos.y)

    if node not in already_processed:
        behavior = calculate_behavior(node)
        node.alignment_behavior = behavior
        already_processed.append(node)

    node.alignment_behavior.setup(output_node)
