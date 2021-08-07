from __future__ import annotations

from typing import TYPE_CHECKING, List, Tuple

from bw_tools.common import bw_chain_dimension
from bw_tools.common.bw_node import Float2

from .alignment_behavior import VerticalAlignMidPoint, VerticalAlignFarthestInput

if TYPE_CHECKING:
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
    # alignment = VerticalAlignMidPoint()
    alignment = VerticalAlignFarthestInput()
    alignment.exec(node)


def stack_inputs(node: LayoutNode):
    input_node: LayoutNode
    for i, input_node in enumerate(node.input_nodes):
        if i == 0:
            align_in_line(input_node, node)
            input_node.update_all_chain_positions()
            continue
        else:
            align_below_shortest_chain_dimension(input_node, node, i)
            if input_node.alignment_behavior.offset_node is node:
                new_pos = Float2(input_node.pos.x, input_node.pos.y)
                input_node.alignment_behavior.update_offset(new_pos)
            input_node.update_all_chain_positions()
            if node.identifier == 1:
                raise AttributeError()
    return


def align_in_line(input_node: LayoutNode, target_node: LayoutNode):
    input_node.set_position(input_node.pos.x, target_node.pos.y)


def align_below_bound(
    node: LayoutNode, lower_bound: float, upper_bound: float
):
    offset = lower_bound - upper_bound
    node.set_position(node.pos.x, node.pos.y + offset)


def align_below_shortest_chain_dimension(
    node_to_move: LayoutNode, output_node: LayoutNode, index: int
):
    node_above = _calculate_node_above(node_to_move, output_node, index)
    node_above_node_list, roots = calculate_node_list(
        node_above, nodes_to_ignore=[node_to_move]
    )
    node_to_move_node_list, _ = calculate_node_list(
        node_to_move, nodes_to_ignore=roots
    )
    smallest_cd = _calculate_smallest_chain_dimension(
        node_to_move, node_above, node_to_move_node_list, node_above_node_list
    )
    upper_bound = _calculate_upper_bounds(
        node_to_move, node_to_move_node_list, smallest_cd
    )
    lower_bound = _calculate_lower_bounds(
        node_above, node_above_node_list, smallest_cd
    )
    align_below_bound(node_to_move, lower_bound + SPACER, upper_bound)


def _calculate_smallest_chain_dimension(
    node_to_move: LayoutNode,
    node_above: LayoutNode,
    node_to_move_chain: bw_chain_dimension.ChainDimension,
    node_above_chain: bw_chain_dimension.ChainDimension,
) -> bw_chain_dimension.ChainDimension:
    node_to_move_cd = bw_chain_dimension.calculate_chain_dimension(
        node_to_move, node_to_move_chain
    )
    nove_above_cd = bw_chain_dimension.calculate_chain_dimension(
        node_above, node_above_chain
    )
    return _get_smaller_chain(node_to_move_cd, nove_above_cd)


def _get_smaller_chain(
    a_cd: bw_chain_dimension.ChainDimension,
    b_cd: bw_chain_dimension.ChainDimension,
) -> bw_chain_dimension.ChainDimension:
    smallest = a_cd
    if a_cd.bounds.left > b_cd.bounds.left:
        smallest = a_cd
    elif a_cd.bounds.left == b_cd.bounds.left:
        if a_cd.bounds.upper >= b_cd.bounds.upper:
            smallest = a_cd
        else:
            smallest = b_cd
    else:
        smallest = b_cd
    return smallest


def _calculate_upper_bounds(
    node_to_move: LayoutNode,
    node_to_move_chain: bw_chain_dimension.ChainDimension,
    smallest_cd: bw_chain_dimension.ChainDimension,
) -> float:
    try:
        limit_bounds = bw_chain_dimension.Bound(left=smallest_cd.bounds.left)
        upper_bound_cd = bw_chain_dimension.calculate_chain_dimension(
            node_to_move, chain=node_to_move_chain, limit_bounds=limit_bounds
        )
    except bw_chain_dimension.OutOfBoundsError:
        # This occurs when the node to move is behind the chain above.
        # This happens because the node to move is a root
        return node_to_move.pos.y - node_to_move.height / 2
    else:
        return upper_bound_cd.bounds.upper


def _calculate_lower_bounds(
    node_above: LayoutNode,
    node_above_chain: bw_chain_dimension.ChainDimension,
    smallest_cd: bw_chain_dimension.ChainDimension,
) -> float:
    try:
        limit_bounds = bw_chain_dimension.Bound(left=smallest_cd.bounds.left)
        lower_bound_cd = bw_chain_dimension.calculate_chain_dimension(
            node_above, chain=node_above_chain, limit_bounds=limit_bounds
        )
    except bw_chain_dimension.OutOfBoundsError:
        # This can also happen when the node above is a root
        return node_above.pos.y + node_above.height / 2
    else:
        return lower_bound_cd.bounds.lower


def calculate_node_list(
    node: LayoutNode, nodes_to_ignore=[]
) -> Tuple[List[LayoutNode], List[LayoutNode]]:
    nodes = [node]
    roots = []
    if node.is_root or node.has_branching_outputs:
        roots.append(node)

    _populate_node_list(node, nodes, roots, nodes_to_ignore)
    return nodes, roots


def _populate_node_list(
    output_node: LayoutNode,
    nodes: List[LayoutNode],
    roots: List[LayoutNode],
    nodes_to_ignore: List[LayoutNode],
):
    input_node: LayoutNode
    for input_node in output_node.input_nodes:
        if (
            input_node in nodes_to_ignore
            or input_node.alignment_behavior.offset_node is not output_node
        ):
            continue

        if (
            input_node.is_root
            or input_node.has_branching_outputs
            and input_node not in roots
        ):
            roots.append(input_node)

        if input_node not in nodes:
            nodes.append(input_node)
            _populate_node_list(input_node, nodes, roots, nodes_to_ignore)


def _calculate_node_above(
    node_to_move: LayoutNode, output_node: LayoutNode, index: int
) -> LayoutNode:
    node_above = output_node.input_nodes[index - 1]

    # If the node_to_move connects to the node above, the want to ignore it.
    # Instead we want to move the node_to_move to the next chain above it in
    # the node_above
    if (
        node_above in node_to_move.output_nodes
        and node_above.has_branching_inputs
    ):
        # If the node above only has the one input, it has to be the
        # node_to_move. Therefore, no sibling chain to move too
        for i, input_node in enumerate(node_above.input_nodes):
            if input_node is node_to_move:
                node_above = node_above.input_nodes[i - 1]

    return node_above
