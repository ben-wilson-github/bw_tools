from abc import ABC
from abc import abstractmethod

from typing import Tuple

from common import bw_node
from common import bw_node_selection
from common import bw_chain_dimension


SPACER = 32


class AbstractAlignStrategy(ABC):
    @abstractmethod
    def align_children(self, parent_node: bw_node.Node):
        pass

class AlignAverage(AbstractAlignStrategy):
    def align_children(self, parent_node: bw_node.Node):
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


def calculate_chain_dimension3(node: bw_node.Node):
    cd = bw_chain_dimension.ChainDimension(
        max_x=node.position.x + (node.width / 2),
        min_x=node.position.x - (node.width / 2),
        max_y=node.position.y + (node.height / 2),
        min_y=node.position.y - (node.height / 2)
    )

    if node.has_input_nodes_connected:
        for input_node in node.input_nodes:
            input_cd = calculate_chain_dimension3(input_node)

            cd.min_x = min(input_cd.min_x, cd.min_x)
            cd.min_y = min(input_cd.min_y, cd.min_y)
            cd.max_x = max(input_cd.max_x, cd.max_x)
            cd.max_y = max(input_cd.max_y, cd.max_y)
    
    return cd

def arrange_children_in_y_axis(parent_node: bw_node.Node):
    for i, input_node in enumerate(parent_node.input_nodes):
        if i == 0:
            input_node.move_to_node(parent_node, offset_x=-(input_node.width + SPACER))
        else:
            node_above = parent_node.input_nodes[i - 1]
            offset = (node_above.height / 2) + (input_node.height / 2) + SPACER
            input_node.move_to_node(node_above, offset_y=offset)

        if input_node.has_input_nodes_connected:
            arrange_children_in_y_axis(input_node)
    
    if parent_node.input_node_count > 1:
        strategy = AlignAverage()
        strategy.align_children(parent_node)


def run(node_selection: bw_node_selection.NodeSelection):
    # TODO: Change to single node selection roots by spliting selections
    root_node = node_selection.root_nodes[0]
    arrange_children_in_y_axis(root_node)
    return
