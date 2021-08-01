from typing import List

from bw_tools.common.bw_node import Node

from .alignment_behavior import (AverageToOutputsYAxis, NodeAlignmentBehavior,
                                 StaticAlignment)

SPACER = 32


def run_sort(node: Node, already_processed: List[Node]):
    for input_node in node.input_nodes:
        process_node(input_node, node, already_processed)
        run_sort(input_node, already_processed)


def process_node(node: Node, output_node: Node, already_processed: List[Node]):
    offset = get_offset_value(node, node.closest_output_node_in_x)
    node.set_position(node.closest_output_node_in_x.pos.x - offset,
                      node.closest_output_node_in_x.pos.y)

    if node not in already_processed:
        behavior = calculate_behavior(node)
        node.alignment_behavior = behavior
        already_processed.append(node)

    node.alignment_behavior.setup(output_node)


def get_offset_value(node: Node, output_node: Node) -> float:
    if node.is_root:
        spacer = SPACER * 4
    else:
        spacer = SPACER
    half_output = output_node.width / 2
    half_input = node.width / 2
    return half_output + spacer + half_input


def calculate_behavior(node: Node) -> NodeAlignmentBehavior:
    if not node.is_root:
        return StaticAlignment()

    for output_node in node.output_nodes:
        # There is another root node in the chain
        indices = node.indices_in_output(output_node)
        if (output_node.chain_contains_root(skip_indices=indices)
                or output_node.chain_contains_branching_inputs(skip_indices=indices)):
            return StaticAlignment()
    return AverageToOutputsYAxis()



