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

class AlignCenter(AbstractAlignStrategy):
    def align_children(self, parent_node: bw_node.Node):
        """Aligns the children of a parent node to the center point of those children in Y"""
        top_child = parent_node.input_nodes[0]
        bottom_child = parent_node.input_nodes[-1]

        min = top_child.position.y - (top_child.height / 2)
        max = bottom_child.position.y + (bottom_child.height / 2)
        mid = (min + max) / 2
        delta = parent_node.position.y - mid

        for input_node in parent_node.input_nodes:
            input_node.set_position(input_node.position.x, input_node.position.y + delta)

            if input_node.has_input_nodes_connected:
                self.align_children(input_node)

def position_children(parent_node: bw_node.Node):
    for i, input_node in enumerate(parent_node.input_nodes):
        if i == 0:
            input_node.move_to_node(parent_node, offset_x=-(input_node.width + SPACER))
        else:
            node_above = parent_node.input_nodes[i - 1]
            above_cd = bw_chain_dimension.calculate_chain_dimension(node_above)

            new_pos_x = parent_node.position.x - (input_node.width + SPACER)
            new_pos_y = parent_node.position.y
            if new_pos_y < above_cd.max_y + SPACER:
                new_pos_y = above_cd.max_y + SPACER + input_node.height / 2
                input_node.set_position(new_pos_x, new_pos_y)

        if input_node.has_input_nodes_connected:
            position_children(input_node)
    
    if parent_node.input_node_count > 1:
        strategy = AlignCenter()
        strategy.align_children(parent_node)

def run(node_selection: bw_node_selection.NodeSelection):
    # TODO: Change to single node selection roots by spliting selections
    root_node = node_selection.root_nodes[0]
    position_children(root_node)
    _run_remove_overlap(root_node)
 
def _run_remove_overlap(parent_node: bw_node.Node):
    for i, input_node in enumerate(parent_node.input_nodes):
        if i != 0:
            cd = bw_chain_dimension.calculate_chain_dimension(input_node)

            node_above = parent_node.input_nodes[i - 1]
            above_cd = bw_chain_dimension.calculate_chain_dimension(
                node_above,
                limit_bounds=bw_chain_dimension.Bound(
                    min_x=cd.min_x
                )
            )
            cd = bw_chain_dimension.calculate_chain_dimension(
                input_node,
                limit_bounds=bw_chain_dimension.Bound(
                min_x=above_cd.min_x
                )
            )

            cd_delta = (input_node.position.y - input_node.height / 2) - cd.min_y

            new_pos_y = above_cd.max_y + input_node.height / 2 + SPACER + cd_delta
            _update_children(input_node, new_pos_y - input_node.position.y)
            input_node.set_position(input_node.position.x, new_pos_y)
        
        _run_remove_overlap(input_node)

        
def _update_children(parent_node: bw_node.Node, offset: float):
    for input_node in parent_node.input_nodes:
        input_node.set_position(input_node.position.x, input_node.position.y + offset)
        _update_children(input_node, offset)