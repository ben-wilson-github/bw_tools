import importlib
from abc import ABC
from abc import abstractmethod

from typing import Tuple
from typing import List

from common import bw_node
from common import bw_node_selection
from common import bw_chain_dimension

importlib.reload(bw_chain_dimension)


SPACER = 32


class AlignCenter():
    @staticmethod
    def calculate_mid_point(a: bw_node.Node, b: bw_node.Node) -> float:
        x = (a.position.x + b.position.x) / 2
        y = (a.position.y + b.position.y) / 2

        return x, y


class AbstractAlignStrategy(ABC):
    @abstractmethod
    def align(self, parent_node: bw_node.Node):
        pass


class AlignParentToCenter(AbstractAlignStrategy, AlignCenter):
    def align(self, parent_node: bw_node.Node):
        _, y = self.calculate_mid_point(parent_node.input_nodes[0], parent_node.input_nodes[-1])
        parent_node.set_position(parent_node.position.x, y)


class AlignChildrenToCenter(AbstractAlignStrategy, AlignCenter):
    def align(self, parent_node: bw_node.Node):
        """Aligns the children of a parent node to the center point of those children in Y"""
        _, y = self.calculate_mid_point(parent_node.input_nodes[0], parent_node.input_nodes[-1])
        offset = y - parent_node.position.y
        seen = []
        offset_children(parent_node, offset=-offset, seen=seen)


def run(node_selection: bw_node_selection.NodeSelection):
    # TODO: Change to single node selection roots by spliting selections
    
    root_node = node_selection.root_nodes[0]

    queue = [root_node]
    while queue:
        node = queue.pop(0)
        layout_x_axis(node, queue)

    layout_y_axis(root_node)
    remove_overlap_in_children(root_node)


def layout_x_axis(parent_node: bw_node.Node, queue: List[bw_node.Node]):
    for input_node in parent_node.input_nodes:
        queue.append(input_node)
        input_node.set_position((parent_node.position.x - parent_node.width / 2) - SPACER - (input_node.width / 2) , input_node.position.y)


def layout_y_axis(node: bw_node.Node):
    for i, input_node in enumerate(node.input_nodes):
        new_pos_y = node.position.y
        if i != 0:
            node_above = node.input_nodes[i - 1]
            
            try:
                above_cd = bw_chain_dimension.calculate_chain_dimension(
                    node_above,
                    limit_bounds=bw_chain_dimension.Bound(
                        left=input_node.position.x
                    )
                )
            except AttributeError:
                pass
            else:
                new_pos_y = above_cd.bounds.lower + SPACER + input_node.height / 2
        
        input_node.set_position(input_node.position.x, new_pos_y)

        if input_node.has_input_nodes_connected:
            layout_y_axis(input_node)
    
    if node.input_node_count > 1:
        strategy = AlignChildrenToCenter()
        strategy.align(node)


def remove_overlap(parent_node: bw_node.Node):
    for i, input_node in enumerate(parent_node.input_nodes):
        if i != 0:
            node_above = parent_node.input_nodes[i - 1]

            smallest_cd = calculate_smallest_chain_dimension(input_node, node_above)
            
            # caluclate chain dimension to find node at highest relevant node
            input_cd = bw_chain_dimension.calculate_chain_dimension(
                input_node,
                limit_bounds=bw_chain_dimension.Bound(
                    left=smallest_cd.bounds.left
                )
            )
            highest_node = input_cd.upper_node

            # calculate chain dimension to find lowest relevant bound
            above_cd = bw_chain_dimension.calculate_chain_dimension(
                node_above,
                limit_bounds=bw_chain_dimension.Bound(
                    left=highest_node.position.x
                )
            )

            offset = (above_cd.bounds.lower + SPACER) - input_cd.bounds.upper
            offset_children(input_node, offset=offset)
            input_node.set_position(input_node.position.x, input_node.position.y + offset)
        
        remove_overlap(input_node)
    
    if parent_node.has_input_nodes_connected:
        if parent_node.is_root:  # Root node
            strategy = AlignChildrenToCenter()
        else:
            strategy = AlignParentToCenter()
        strategy.align(parent_node)

def remove_overlap_in_children(parent_node: bw_node.Node):
    for i, input_node in enumerate(parent_node.input_nodes):
        if i != 0:
            node_above = parent_node.input_nodes[i - 1]

            smallest_cd = calculate_smallest_chain_dimension(input_node, node_above)
            smallest_cd.right_node.add_comment('I am smaller chain')
            smallest_cd.left_node.add_comment('I am smallest left node')

            # caluclate chain dimension to find node at highest relevant node
            # from the input chain
            This all needs tidy up
            try:
                input_cd = bw_chain_dimension.calculate_chain_dimension(
                    input_node,
                    limit_bounds=bw_chain_dimension.Bound(
                        left=smallest_cd.bounds.left
                    )
                )
            except AttributeError:
                highest_node = input_node
                highest_bounds_from_input_chain = input_node.position.y - input_node.height / 2
            else:
                highest_node = input_cd.upper_node
                highest_bounds_from_input_chain = input_cd.bounds.upper
            highest_node.add_comment('I am highest Node in the input chain')

            try:
                # calculate chain dimension to find lowest relevant bound
                above_cd = bw_chain_dimension.calculate_chain_dimension(
                    node_above,
                    limit_bounds=bw_chain_dimension.Bound(
                        left=highest_node.position.x
                    ),
                    break_on_branch=True
                )
            except AttributeError:
                lowest_node = node_above
                lowest_bounds_from_chain_above = node_above.position.y + node_above.height / 2
            else:
                lowest_node = above_cd.lower_node
                lowest_bounds_from_chain_above = above_cd.bounds.lower
            lowest_node.add_comment('I am the lowest node in the chain above')

            offset = (lowest_bounds_from_chain_above + SPACER) - highest_bounds_from_input_chain
            seen = []
            offset_children_with_break(input_node, offset=offset, seen=seen)
            input_node.set_position(input_node.position.x, input_node.position.y + offset)
        
        remove_overlap_in_children(input_node)
    
    # if parent_node.has_input_nodes_connected:
    #     if parent_node.is_root:  # Root node
    #         strategy = AlignChildrenToCenter()
    #     else:
    #         strategy = AlignParentToCenter()
    #     strategy.align(parent_node)

     
def offset_children(parent_node: bw_node.Node, offset: float, seen: List[bw_node.Node]):
    for input_node in parent_node.input_nodes:
        if input_node in seen:
            continue

        input_node.set_position(input_node.position.x, input_node.position.y + offset)
        seen.append(input_node)
        offset_children(input_node, offset, seen)

def offset_children_with_break(parent_node: bw_node.Node, offset: float, seen: List[bw_node.Node]):
    for input_node in parent_node.input_nodes:
        if input_node in seen or input_node.output_node_count > 1:
            continue

        input_node.set_position(input_node.position.x, input_node.position.y + offset)
        seen.append(input_node)
        offset_children_with_break(input_node, offset, seen)


def calculate_smallest_chain_dimension(a: bw_node.Node, b: bw_node.Node) -> bw_chain_dimension.ChainDimension:
    a_cd = bw_chain_dimension.calculate_chain_dimension(a, break_on_branch=True)
    b_cd = bw_chain_dimension.calculate_chain_dimension(b, break_on_branch=True)
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
