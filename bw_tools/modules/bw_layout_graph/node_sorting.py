from .alignment_behavior import StaticAlignment
from .layout_node import LayoutNode
from bw_tools.modules.bw_layout_graph import layout_node
from bw_tools.common import bw_chain_dimension
from . import aligner
from typing import List

SPACER = 32

def position_nodes_mainline(output_node: LayoutNode):
    # do the initial position
    position_nodes(output_node)

    if not output_node.has_input_nodes_connected:
        return

    mainline_node = output_node.input_nodes[0]
    if output_node.has_branching_inputs:
        mainline_node = calculate_mainline_node(output_node)
    print(mainline_node)



def calculate_mainline_node(output_node: LayoutNode):
    cds: List[bw_chain_dimension.ChainDimension] = list()
    for input_node in output_node.input_nodes:
        chain = get_node_chain(input_node)
        cds.append(bw_chain_dimension.calculate_chain_dimension(input_node, chain))
    
    cds.sort(key=lambda x: x.bounds.left)
    return cds[0].right_node


def get_node_chain(node: LayoutNode):
    def _populate_chain(node: LayoutNode):
        for input_node in node.input_nodes:
            if input_node.has_branching_outputs:
                continue
            chain.append(input_node)
            _populate_chain(input_node)
    chain = [node]
    _populate_chain(node)
    return chain
    



def position_nodes(output_node: LayoutNode):
    input_node: LayoutNode
    for input_node in output_node.input_nodes:
        input_node.set_position(
            input_node.closest_output_node_in_x.pos.x
            - get_offset_value(
                input_node, input_node.closest_output_node_in_x
            ),
            input_node.farthest_output_nodes_in_x[0].pos.y
        )
        position_nodes(input_node)


def build_alignment_behaviors(output_node: LayoutNode):
    input_node: LayoutNode
    for input_node in output_node.input_nodes:
        if input_node.alignment_behavior is None:
            input_node.alignment_behavior = StaticAlignment(input_node)

        if output_node.pos.x > input_node.alignment_behavior.offset_node.pos.x:
            input_node.alignment_behavior.offset_node = output_node
            input_node.alignment_behavior.update_offset(input_node.pos)
        build_alignment_behaviors(input_node)


def get_offset_value(node: LayoutNode, output_node: LayoutNode) -> float:
    if node.has_branching_outputs:
        spacer = SPACER  # * 4
    else:
        spacer = SPACER
    half_output = output_node.width / 2
    half_input = node.width / 2
    return half_output + spacer + half_input
