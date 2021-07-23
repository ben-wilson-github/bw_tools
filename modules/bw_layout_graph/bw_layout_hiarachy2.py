import importlib
from abc import ABC
from abc import abstractmethod

from typing import Tuple

from common import bw_node
from common import bw_node_selection
from common import bw_chain_dimension

importlib.reload(bw_chain_dimension)


SPACER = 32


class AbstractAlignStrategy(ABC):
    @abstractmethod
    def align_children(self, parent_node: bw_node.Node):
        pass

class AlignParentCenter(AbstractAlignStrategy):
    def align_children(self, parent_node: bw_node.Node):
        top_child = parent_node.input_nodes[0]
        bottom_child = parent_node.input_nodes[-1]

        min = top_child.position.y - (top_child.height / 2)
        max = bottom_child.position.y + (bottom_child.height / 2)
        mid = (min + max) / 2

        offset = parent_node.position.y - mid
        offset = mid - parent_node.position.y
        parent_node.set_position(parent_node.position.x, parent_node.position.y + offset)


class AlignCenter(AbstractAlignStrategy):
    def align_children(self, parent_node: bw_node.Node):
        """Aligns the children of a parent node to the center point of those children in Y"""
        top_child = parent_node.input_nodes[0]
        bottom_child = parent_node.input_nodes[-1]

        min = top_child.position.y - (top_child.height / 2)
        max = bottom_child.position.y + (bottom_child.height / 2)
        mid = (min + max) / 2
        offset = parent_node.position.y - mid

        offset_children(parent_node, offset=offset)

def arrange_chain_in_hiararchy(parent_node: bw_node.Node):
    for i, input_node in enumerate(parent_node.input_nodes):
        new_pos_x = parent_node.position.x - (input_node.width + SPACER)
        new_pos_y = parent_node.position.y

        if i != 0:
            node_above = parent_node.input_nodes[i - 1]
            above_cd = bw_chain_dimension.calculate_chain_dimension(
                node_above,
                limit_bounds=bw_chain_dimension.Bound(
                    left=input_node.position.x
                )
            )
            new_pos_y = above_cd.bounds.lower + SPACER + input_node.height / 2
        
        input_node.set_position(new_pos_x, new_pos_y)

        if input_node.has_input_nodes_connected:
            arrange_chain_in_hiararchy(input_node)
    
    if parent_node.input_node_count > 1:
        strategy = AlignCenter()
        strategy.align_children(parent_node)

def run(node_selection: bw_node_selection.NodeSelection):
    # TODO: Change to single node selection roots by spliting selections
    root_node = node_selection.root_nodes[0]
    arrange_chain_in_hiararchy(root_node)
    run_remove_overlap(root_node)

def run_remove_overlap(parent_node: bw_node.Node):
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
        
        run_remove_overlap(input_node)
    
    if parent_node.input_node_count > 1:
        if parent_node.output_node_count == 0:
            strategy = AlignCenter()
        else:
            strategy = AlignParentCenter()
        strategy.align_children(parent_node)

     
def offset_children(parent_node: bw_node.Node, offset: float):
    for input_node in parent_node.input_nodes:
        input_node.set_position(input_node.position.x, input_node.position.y + offset)
        offset_children(input_node, offset)

def calculate_smallest_chain_dimension(a: bw_node.Node, b: bw_node.Node) -> bw_chain_dimension.ChainDimension:
    a_cd = bw_chain_dimension.calculate_chain_dimension(a)
    b_cd = bw_chain_dimension.calculate_chain_dimension(b)
    smallest = a_cd
    if a_cd.bounds.left < b_cd.bounds.left:
        smallest = b_cd
    return smallest