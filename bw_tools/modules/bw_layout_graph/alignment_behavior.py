from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Tuple, TYPE_CHECKING, List

from bw_tools.common.bw_node import Float2
from bw_tools.common import bw_chain_dimension

if TYPE_CHECKING:
    from .layout_node import LayoutNode

SPACER = 32


@dataclass
class NodeAlignmentBehavior(ABC):
    _parent: LayoutNode = field(repr=False)
    offset: Float2 = field(default_factory=Float2)
    offset_node: LayoutNode = field(init=False)

    def __post_init__(self):
        self.offset_node = self._parent

    @abstractmethod
    def exec(self):
        pass

    @abstractmethod
    def update_offset(self, new_post: Float2):
        pass


@dataclass
class StaticAlignment(NodeAlignmentBehavior):
    def exec(self):
        self._parent.set_position(
            self.offset_node.pos.x + self.offset.x,
            self.offset_node.pos.y + self.offset.y,
        )

    def update_offset(self, new_pos: Float2):
        self.offset.x = new_pos.x - self.offset_node.pos.x
        self.offset.y = new_pos.y - self.offset_node.pos.y


def calculate_mid_point(a: LayoutNode, b: LayoutNode) -> Tuple[float, float]:
    x = (a.pos.x + b.pos.x) / 2
    y = (a.pos.y + b.pos.y) / 2

    return x, y


def align_in_line(input_node: LayoutNode, target_node: LayoutNode):
    input_node.set_position(input_node.pos.x, target_node.pos.y)


def align_below(node: LayoutNode, target_node: LayoutNode):
    y = (
        target_node.pos.y
        + (target_node.height / 2)
        + SPACER
        + (node.height / 2)
    )
    node.set_position(node.pos.x, y)


def align_above(node: LayoutNode, target_node: LayoutNode):
    y = (
        target_node.pos.y
        - (target_node.height / 2)
        - SPACER
        - (node.height / 2)
    )
    node.set_position(node.pos.x, y)


def align_above_bound(
    node: LayoutNode, lower_bound: float, upper_bound: float
):
    offset = upper_bound - lower_bound
    node.set_position(node.pos.x, node.pos.y + offset)


def align_below_bound(
    node: LayoutNode, lower_bound: float, upper_bound: float
):
    offset = lower_bound - upper_bound
    node.set_position(node.pos.x, node.pos.y + offset)


def align_node_between(node: LayoutNode, top: LayoutNode, bottom: LayoutNode):
    _, mid_point = calculate_mid_point(top, bottom)
    node.set_position(node.pos.x, mid_point)


def _calculate_smallest_chain_dimension(
    node_to_move: LayoutNode,
    node_above: LayoutNode,
    node_to_move_chain: bw_chain_dimension.ChainDimension,
    node_above_chain: bw_chain_dimension.ChainDimension
):
    node_to_move_cd = bw_chain_dimension.calculate_chain_dimension(
        node_to_move, node_to_move_chain
    )
    nove_above_cd = bw_chain_dimension.calculate_chain_dimension(
        node_above, node_above_chain
    )
    return calculate_smallest_chain_dimension(
        node_to_move_cd, nove_above_cd
    )


def align_below_shortest_chain_dimension(
    node_to_move: LayoutNode, output_node: LayoutNode, index: int
):
    node_above = _calculate_node_above(node_to_move, output_node, index)
    node_above_node_list, roots = _calculate_node_list(
        node_above, nodes_to_ignore=[node_to_move]
    )
    node_to_move_node_list, _ = _calculate_node_list(
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


def _calculate_upper_bounds(
    node_to_move: LayoutNode,
    node_to_move_chain: bw_chain_dimension.ChainDimension,
    smallest_cd: bw_chain_dimension.ChainDimension
):
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
    smallest_cd: bw_chain_dimension.ChainDimension
):
    try:
        limit_bounds = bw_chain_dimension.Bound(
            left=smallest_cd.bounds.left
        )
        lower_bound_cd = bw_chain_dimension.calculate_chain_dimension(
            node_above, chain=node_above_chain, limit_bounds=limit_bounds
        )
    except bw_chain_dimension.OutOfBoundsError:
        # This can also happen when the node above is a root
        return node_above.pos.y + node_above.height / 2
    else:
        return lower_bound_cd.bounds.lower


def _calculate_node_list(node: LayoutNode, nodes_to_ignore=[]) -> Tuple[List[LayoutNode], List[LayoutNode]]:
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
    nodes_to_ignore: List[LayoutNode]
):
    input_node: LayoutNode
    for input_node in output_node.input_nodes:
        if input_node in nodes_to_ignore or input_node.alignment_behavior.offset_node is not output_node:
            continue

        if (
            input_node.is_root
            or input_node.has_branching_outputs
            and input_node not in roots
        ):
            roots.append(input_node)

        if (input_node not in nodes
        ):
            nodes.append(input_node)
            _populate_node_list(input_node, nodes, roots, nodes_to_ignore)


def calculate_smallest_chain_dimension(
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


def _calculate_node_above(
    node_to_move: LayoutNode, output_node: LayoutNode, index: int
):
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
