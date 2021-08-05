from abc import ABC
from abc import abstractmethod
from dataclasses import Field, dataclass, field, fields

from typing import Tuple
from typing import List

from bw_tools.common.bw_node import Node
from bw_tools.common.bw_node import Float2
from bw_tools.common import bw_node_selection
from bw_tools.common import bw_chain_dimension

from . import utils
from . import post_alignment_behavior as pab
from . import alignment_behavior as ab


SPACER = 32


@dataclass
class NodeAlignmentBehavior(ABC):
    parent: Node = None
    @abstractmethod
    def exec(self):
        pass

    @abstractmethod
    def setup(self, node: Node):
        pass


@dataclass
class StaticAlignment(NodeAlignmentBehavior):
    offset: Float2 = field(default_factory=Float2)
    offset_node: Node = None

    def exec(self):
        self.parent.set_position(
            self.offset_node.pos.x + self.offset.x,
            self.offset_node.pos.y + self.offset.y
        )

    def setup(self, node: Node):
        """Updates the offset node if the node passed in is further forward than the current offset parent.
        Updates the offset"""
        if self.offset_node is None:
            self.offset_node = node
        elif node.pos.x > self.offset_node.pos.x:
            self.offset_node = node
        self.update_offset(self.parent.pos)

    def update_offset(self, new_pos: Float2):
        self.offset.x = new_pos.x - self.offset_node.pos.x
        self.offset.y = new_pos.y - self.offset_node.pos.y

@dataclass
class AverageToOutputsYAxis(NodeAlignmentBehavior):
    top_node: Node = None
    bottom_node: Node = None

    def exec(self):
        _, y = utils.calculate_mid_point(self.top_node, self.bottom_node)
        self.parent.set_position(self.parent.pos.x, y)

    def setup(self, _: Node):
        if self.top_node is None or self.bottom_node is None:
            sorted_outputs = sorted(list(self.parent.output_nodes), key=lambda x: x.pos.y)
            self.top_node = sorted_outputs[0]
            self.bottom_node = sorted_outputs[-1]
    


def align_in_line(input_node: Node, target_node: Node):
    input_node.set_position(input_node.pos.x, target_node.pos.y)


def align_below(node: Node, target_node: Node):
    y = target_node.pos.y + (target_node.height / 2) + SPACER + (node.height / 2)
    node.set_position(node.pos.x, y)


def align_above(node: Node, target_node: Node):
    y = target_node.pos.y - (target_node.height / 2) - SPACER - (node.height / 2)
    node.set_position(node.pos.x, y)


def align_above_bound(node: Node, lower_bound: float, upper_bound: float):
    offset = upper_bound - lower_bound
    node.set_position(node.pos.x, node.pos.y + offset)


def align_below_bound(node: Node, lower_bound: float, upper_bound: float):
    offset = lower_bound - upper_bound
    node.set_position(node.pos.x, node.pos.y + offset)


def align_node_between(node: Node, top: Node, bottom: Node):
    _, mid_point = utils.calculate_mid_point(top, bottom)
    node.set_position(node.pos.x, mid_point)

def align_above_shortest_chain_dimension(node: Node, output_node: Node, index: int, node_selection):
    node_list = list(output_node.input_nodes)
    node_list.reverse()
    node_below = node_list[index - 1]
    node_to_move = node

    if output_node.identifier == 1:
        print('a')

    node_to_move_chain, roots = get_chain(node_to_move, nodes_to_ignore=[node_below])
    node_below_chain, _ = get_chain(node_below, nodes_to_ignore=roots)


    # node_to_move_cd = bw_chain_dimension.calculate_chain_dimension(node_to_move, node_to_move.chain)
    # nove_above_cd = bw_chain_dimension.calculate_chain_dimension(node_above, node_above.chain)
    node_to_move_cd = bw_chain_dimension.calculate_chain_dimension(node_to_move, node_to_move_chain)
    nove_above_cd = bw_chain_dimension.calculate_chain_dimension(node_below, node_below_chain)

    smallest_cd = calculate_smallest_chain_dimension(node_to_move_cd, nove_above_cd)
    
    try:
        limit_bounds = bw_chain_dimension.Bound(left=smallest_cd.bounds.left)
        # upper_bound_cd = bw_chain_dimension.calculate_chain_dimension(node_to_move, chain=node_to_move.chain, limit_bounds=limit_bounds)
        upper_bound_cd = bw_chain_dimension.calculate_chain_dimension(node_below, chain=node_below_chain, limit_bounds=limit_bounds)
    except bw_chain_dimension.OutOfBoundsError:
        # This occur when the node to move is behind the chain above. This happens because the node to move is a root
        upper_bound = node_below.pos.y - node_below.height / 2
        upper_node = node_below
    else:
        upper_bound = upper_bound_cd.bounds.upper
        upper_node = upper_bound_cd.upper_node
    
    # if output_node.identifier == 1420079326:
    #     upper_node.add_comment('I am upper node')

    try:
        # limit_bounds = bw_chain_dimension.Bound(left=upper_node.pos.x)
        limit_bounds = bw_chain_dimension.Bound(left=smallest_cd.bounds.left) # This is for stacking
        # lower_bound_cd = bw_chain_dimension.calculate_chain_dimension(node_above, chain=node_above.chain, limit_bounds=limit_bounds)
        lower_bound_cd = bw_chain_dimension.calculate_chain_dimension(node_to_move, chain=node_to_move_chain, limit_bounds=limit_bounds)
    except bw_chain_dimension.OutOfBoundsError:
        # This can also happen when the node above is a root
        lower_bound = node_to_move.pos.y + node_to_move.height / 2
    else:
        lower_bound = lower_bound_cd.bounds.lower
    
    # if output_node.identifier == 1420079326:
    #     lower_bound_cd.lower_node.add_comment('I am lower node')

    ab.align_above_bound(node_to_move, lower_bound + SPACER, upper_bound)


def align_below_shortest_chain_dimension(node: Node, output_node: Node, index: int, node_selection):
    node_list = output_node.input_nodes
    node_above = node_list[index - 1]
    node_to_move = node

    if output_node.identifier == 1420163229:
        print('a')
        # raise ArithmeticError()

    # If the node_to_move connects to the node above, the want to ignore it.
    # Instead we want to move the node_to_move to the next chain above it in the node_above
    if node_above in node_to_move.output_nodes:
        if node_above.input_node_count > 1: # If the node above only has the one input, it has to be the node_to_move.
            # and therefore, no sibling chain to move too
            for i, input_node in enumerate(node_above.input_nodes):
                if input_node is node_to_move:
                    node_above = node_above.input_nodes[i - 1]
    
    
    node_above_chain, roots = get_chain(node_above, nodes_to_ignore=[node_to_move])
    # roots = [] # chain 3 doesnt want roots, because vector warp grayscale is in the chain we are moving below
    node_to_move_chain, _ = get_chain(node_to_move, nodes_to_ignore=roots)

    # node_to_move.update_all_chain_positions_only_for_offset_parent()

    if output_node.identifier == 1:
        raise ArithmeticError()

    # This is to remove uneceassy padding
    # if node_to_move.alignment_behavior.offset_node is not output_node:
    #     node_to_move_chain = [node_to_move]
    

    # node_to_move_cd = bw_chain_dimension.calculate_chain_dimension(node_to_move, node_to_move.chain)
    # nove_above_cd = bw_chain_dimension.calculate_chain_dimension(node_above, node_above.chain)
    node_to_move_cd = bw_chain_dimension.calculate_chain_dimension(node_to_move, node_to_move_chain)
    nove_above_cd = bw_chain_dimension.calculate_chain_dimension(node_above, node_above_chain)

    smallest_cd = calculate_smallest_chain_dimension(node_to_move_cd, nove_above_cd)
    
    try:
        limit_bounds = bw_chain_dimension.Bound(left=smallest_cd.bounds.left)
        # upper_bound_cd = bw_chain_dimension.calculate_chain_dimension(node_to_move, chain=node_to_move.chain, limit_bounds=limit_bounds)
        upper_bound_cd = bw_chain_dimension.calculate_chain_dimension(node_to_move, chain=node_to_move_chain, limit_bounds=limit_bounds)
    except bw_chain_dimension.OutOfBoundsError:
        # This occur when the node to move is behind the chain above. This happens because the node to move is a root
        upper_bound = node_to_move.pos.y - node_to_move.height / 2
        upper_node = node_to_move
    else:
        upper_bound = upper_bound_cd.bounds.upper
        upper_node = upper_bound_cd.upper_node
    
    # if output_node.identifier == 1420079326:
    #     upper_node.add_comment('I am upper node')

    try:
        # limit_bounds = bw_chain_dimension.Bound(left=upper_node.pos.x)
        limit_bounds = bw_chain_dimension.Bound(left=smallest_cd.bounds.left) # This is for stacking
        # lower_bound_cd = bw_chain_dimension.calculate_chain_dimension(node_above, chain=node_above.chain, limit_bounds=limit_bounds)
        lower_bound_cd = bw_chain_dimension.calculate_chain_dimension(node_above, chain=node_above_chain, limit_bounds=limit_bounds)
    except bw_chain_dimension.OutOfBoundsError:
        # This can also happen when the node above is a root
        lower_bound = node_above.pos.y + node_above.height / 2
    else:
        lower_bound = lower_bound_cd.bounds.lower
    
    # if output_node.identifier == 1420079326:
    #     lower_bound_cd.lower_node.add_comment('I am lower node')

    ab.align_below_bound(node_to_move, lower_bound + SPACER, upper_bound)

def get_chain(node: Node, nodes_to_ignore=[]):
    def _get_chain(node, nodes, roots, nodes_to_ignore):
        input_node: Node
        for input_node in node.input_nodes:
            if input_node in nodes_to_ignore:
                # if input_node.alignment_behavior.offset_node is node:
                #     nodes.append(input_node)
                continue

            if input_node.is_root and input_node not in roots and input_node.alignment_behavior.offset_node is node:
                roots.append(input_node)
            # if input_node.is_root and input_node not in roots:
            #     roots.append(input_node)
            
            if input_node.alignment_behavior.offset_node is node and input_node not in nodes:
                nodes.append(input_node)
                _get_chain(input_node, nodes, roots, nodes_to_ignore)

            # if input_node not in nodes:
            #     nodes.append(input_node)
            # _get_chain(input_node, nodes, roots, nodes_to_ignore)
    
    nodes = [node]
    roots = []
    if node.is_root:
        roots.append(node)
    _get_chain(node, nodes, roots, nodes_to_ignore)
    return nodes, roots

    
def calculate_smallest_chain_dimension(
        a_cd: bw_chain_dimension.ChainDimension,
        b_cd: bw_chain_dimension.ChainDimension) -> bw_chain_dimension.ChainDimension:
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
