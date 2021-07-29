from abc import ABC
from abc import abstractmethod
from dataclasses import dataclass
from typing import Tuple
from typing import List

from common import bw_node
from common import bw_chain_dimension
from . import input_alignment_behavior as iab
from . import utils


@dataclass
class PostAlignmentBehavior(ABC):
    """
    Defines the behavior to execute after alignment of each input node is
    finished.
    """
    @abstractmethod
    def run(self, node: bw_node.Node):
        pass


class NoPostAlignment(PostAlignmentBehavior):
    def run(self, _):
        pass


def average_positions_relative_to_node(node_list: List[bw_node.Node], target_node: bw_node.Node):
    _, mid_point = utils.calculate_mid_point(node_list[0],
                                             node_list[-1])
    offset = target_node.pos.y - mid_point

    node: bw_node.Node
    for node in node_list:
        node.set_position(node.pos.x, node.pos.y + offset)


@dataclass
class AlignInputsToCenterPoint(PostAlignmentBehavior):
    def run(self, node: bw_node.Node):
        inputs = self.get_nodes(node)

        if len(inputs) < 2:
            return

        top_input_node = inputs[0]
        bottom_input_node = inputs[-1]
        print(f'Mid point is between {top_input_node} and {bottom_input_node}')
        print(f'Will move inputs of {node}')
        print(f'Which is {inputs}')
        _, mid_point = utils.calculate_mid_point(top_input_node,
                                                 bottom_input_node)

        offset = node.pos.y - mid_point

        input_node: bw_node.Node
        for input_node in inputs:
            print(f'Moving {input_node.label}')
            input_node.set_position(input_node.pos.x,
                                    input_node.pos.y + offset)
            input_node.update_offset_to_node(node)
            self.on_after_position_node(input_node)

        if node.identifier == 1419544088:
            raise AttributeError()

    @abstractmethod
    def on_after_position_node(self, input_node: bw_node.Node):
        pass

    @abstractmethod
    def get_nodes(self, node: bw_node.Node) -> List[bw_node.Node]:
        pass


class AlignInputsToCenterPointUpdateChain(AlignInputsToCenterPoint):
    def get_nodes(self, node: bw_node.Node) -> List[bw_node.Node]:
        return node.input_nodes

    def on_after_position_node(self, input_node: bw_node.Node):
        print(f'node {input_node} ha input_node.offset_node {input_node.offset_node}')
        input_node.refresh_positions()


class AlignChainInputsToCenterPointOneNode(AlignInputsToCenterPoint):
    def on_after_position_node(self, input_node: bw_node.Node):
        pass

    def get_nodes(self, node: bw_node.Node) -> List[bw_node.Node]:
        return node.input_nodes_in_chain


def remove_overlap(node: bw_node.Node, node_list: List[bw_node.Node]):
    print(f'Going to remove overlap in inputs for {node}')
    top_input_node = node_list[0]
    bottom_input_node = node_list[-1]
    _, mid_point = utils.calculate_mid_point(top_input_node,
                                             bottom_input_node)

    nodes_above, nodes_below = get_input_nodes_around_point(
            node_list,
            mid_point
        )
    nodes_above.reverse()
    print(f'Nodes above the mid point {nodes_above}')
    print(f'Nodes below the mid point {nodes_below}')
    for node_above in nodes_above:
        i = node_list.index(node_above)
        node_below = node_list[i + 1]

        node_above_cd = bw_chain_dimension.calculate_chain_dimension(node_above, chain=node_above.chain)
        node_below_cd = bw_chain_dimension.calculate_chain_dimension(node_below, chain=node_below.chain)
        smallest_cd = calculate_smallest_chain_dimension(node_above_cd, node_below_cd)

        limit_bounds = bw_chain_dimension.Bound(left=smallest_cd.bounds.left)
        upper_bound_cd = bw_chain_dimension.calculate_chain_dimension(node_below, chain=node_below.chain, limit_bounds=limit_bounds)
        limit_bounds = bw_chain_dimension.Bound(left=upper_bound_cd.upper_node.pos.x)
        lower_bound_cd = bw_chain_dimension.calculate_chain_dimension(node_above, chain=node_above.chain, limit_bounds=limit_bounds)

        iab.align_above_bound(node_above, lower_bound_cd.bounds.lower, upper_bound_cd.bounds.upper)
        node_above.update_offset_to_node(node)
        node_above.refresh_positions_in_chain()

    for i, node_below in enumerate(nodes_below):
        #TODO: Move into function
        i = node_list.index(node_below)
        node_above = node_list[i - 1]

        node_above_cd = bw_chain_dimension.calculate_chain_dimension(node_above, chain=node_above.chain)
        node_below_cd = bw_chain_dimension.calculate_chain_dimension(node_below, chain=node_below.chain)
        smallest_cd = calculate_smallest_chain_dimension(node_above_cd, node_below_cd)
        
        limit_bounds = bw_chain_dimension.Bound(left=smallest_cd.bounds.left)
        upper_bound_cd = bw_chain_dimension.calculate_chain_dimension(node_below, chain=node_below.chain, limit_bounds=limit_bounds)
        limit_bounds = bw_chain_dimension.Bound(left=upper_bound_cd.upper_node.pos.x)
        lower_bound_cd = bw_chain_dimension.calculate_chain_dimension(node_above, chain=node_above.chain, limit_bounds=limit_bounds)
        
        iab.align_below_bound(node_below, lower_bound_cd.bounds.lower, upper_bound_cd.bounds.upper)

        node_above.update_offset_to_node(node)
        node_above.refresh_positions_in_chain()
    
    average_positions_relative_to_node(node_list, node)

    # # Update all offset data
    for input_node in node_list:
        input_node.update_offset_to_node(node)
        input_node.refresh_positions()


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


class AlignNoOverlapAverageCenter(PostAlignmentBehavior):
    def run(self, node: bw_node.Node):
        if node.input_nodes_in_chain_count < 2:
            return

        top_input_node = node.input_nodes_in_chain[0]
        bottom_input_node = node.input_nodes_in_chain[-1]
        _, mid_point = utils.calculate_mid_point(top_input_node,
                                                 bottom_input_node)

        nodes_above, nodes_below = get_input_nodes_around_point(
            node,
            mid_point
        )

        nodes_above.reverse()

        for input_node in nodes_above:
            align = input_alignment_behavior.AlignAboveSiblingSmallestChain()
            align.run(input_node, node)
            input_node.update_offset_to_node(input_node.offset_node)
            input_node.refresh_positions()

        for input_node in nodes_below:
            align = input_alignment_behavior.AlignBelowSiblingSmallestChainSameChainInputs()
            align.run(input_node, node)
            input_node.update_offset_to_node(input_node.offset_node)
            input_node.refresh_positions()

        align = AlignInputsToCenterPointUpdateChain()
        align.run(node)

        if node.identifier == 1419572473:
            raise AttributeError()

def get_input_nodes_around_point(
        node_list: List[bw_node.Node],
        point: float
        ) -> Tuple[List[bw_node.Node], List[bw_node.Node]]:
    nodes_above = list()
    nodes_below = list()
    for node in node_list:
        if node.pos.y < point:
            nodes_above.append(node)
        elif node.pos.y > point:
            nodes_below.append(node)
    return nodes_above, nodes_below
