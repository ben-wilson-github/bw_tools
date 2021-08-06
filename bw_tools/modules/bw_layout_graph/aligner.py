from dataclasses import dataclass, field
from typing import List

from bw_tools.common.bw_node import Float2

from . import alignment_behavior
from .layout_node import LayoutNode

SPACER = 32


def run_aligner(node: LayoutNode, already_processed: List[LayoutNode]):
    if not node.has_input_nodes_connected:
        return

    if node in already_processed:
        return

    for input_node in node.input_nodes:
        run_aligner(input_node, already_processed)

    if node.has_branching_inputs:
        already_processed.append(node)
        process_node(node)


def process_node(node: LayoutNode):
    stack_inputs(node)
    # resolve_alignment_stack(node)
    resolve_alignment_average(node)


# TODO: this can be a stragety
def resolve_alignment_average(node: LayoutNode):
    _, mid_point = alignment_behavior.calculate_mid_point(
        node.input_nodes[0], node.input_nodes[-1]
    )
    offset = node.pos.y - mid_point

    input_node: LayoutNode
    for input_node in node.input_nodes:
        if node is not input_node.alignment_behavior.offset_node:
            # Same as resetting its position
            input_node.alignment_behavior.exec()
        else:
            input_node.alignment_behavior.offset_node = node
            input_node.alignment_behavior.update_offset(
                Float2(input_node.pos.x, input_node.pos.y + offset)
            )
            input_node.alignment_behavior.exec()

        input_node.update_all_chain_positions()
    return


# TODO: this can be a stragety
def resolve_alignment_stack(node: LayoutNode):
    input_node: LayoutNode
    for input_node in node.input_nodes:
        if node is not input_node.alignment_behavior.offset_node:
            # Same as resetting its position
            input_node.alignment_behavior.exec()
        else:
            input_node.alignment_behavior.offset_node = node
            input_node.alignment_behavior.update_offset(input_node.pos)
            input_node.alignment_behavior.exec()

        input_node.update_all_chain_positions()
    return


def stack_inputs(node: LayoutNode):
    input_node: LayoutNode
    for i, input_node in enumerate(node.input_nodes):
        if i == 0:
            alignment_behavior.align_in_line(input_node, node)
            input_node.update_all_chain_positions()
            continue
        else:
            alignment_behavior.align_below_shortest_chain_dimension(
                input_node, node, i
            )
            if input_node.alignment_behavior.offset_node is node:
                new_pos = Float2(input_node.pos.x, input_node.pos.y)
                input_node.alignment_behavior.update_offset(new_pos)
            input_node.update_all_chain_positions()
            if node.identifier == 1:
                raise AttributeError()
    return
