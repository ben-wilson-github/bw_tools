from .alignment_behavior import StaticAlignment
from .layout_node import LayoutNode
from bw_tools.modules.bw_layout_graph import layout_node
from bw_tools.common import bw_chain_dimension
from . import aligner
from typing import List

SPACER = 32

def position_nodes_mainline(output_node: LayoutNode, already_processed: List[LayoutNode]):
    print(output_node)
    if output_node in already_processed:
        return

    for input_node in output_node.input_nodes:
        position_nodes_mainline(input_node, already_processed)

    if output_node.has_branching_inputs:
        push_back_mainline(output_node, already_processed)
        already_processed.append(output_node)

def push_back_mainline(output_node: LayoutNode, already_processed: List[LayoutNode]):
    if output_node.identifier == 1419561060:
        print('a')


    cds: List[bw_chain_dimension.ChainDimension] = get_chain_dimensions(output_node)
    cds.sort(key=lambda x: x.bounds.left)
    print(cds)
    print('==========')
    if len(cds) >= 2:
        mainline_node: LayoutNode = cds[0].right_node
        mainline_node.set_position(
            cds[1].bounds.left - SPACER - (mainline_node.width / 2),
            mainline_node.farthest_output_nodes_in_x[0].pos.y
        )
        mainline_node.alignment_behavior.update_offset(mainline_node.pos)
        mainline_node.update_all_chain_positions_deep()

    if output_node.identifier == 1:
        raise ArithmeticError()
    
    ERROR Test CHAIN 6. 


def get_chain_dimensions2(output_node: LayoutNode):
    cds = list()
    input_node: LayoutNode
    for input_node in output_node.input_nodes:
        if input_node.has_branching_outputs:
            continue
        node_list = get_node_chain_simple(input_node)
        cds.append(bw_chain_dimension.calculate_chain_dimension(input_node, node_list))
    return cds



def get_chain_dimensions(output_node: LayoutNode):
    node_lists = dict()
    input_node: LayoutNode
    for i, input_node in enumerate(output_node.input_nodes):
        if input_node.alignment_behavior.offset_node is not output_node:
            continue
        # If the node is not right next to the output, then its already been pushed back or is a branching node.
        # We dont want to consider those
        # if input_node.pos.x < output_node.pos.x - (output_node.width / 2) - SPACER - (input_node.width / 2):
        #     continue
        node_lists[i] = dict()
        node_list, roots_in_chain = get_node_chain(input_node)
        node_lists[i]['nodes'] = node_list
        node_lists[i]['roots'] = roots_in_chain
    
    if len(node_lists) < 2:
        return []
    
    cds: List[bw_chain_dimension.ChainDimension] = list()
    for i, input_node in enumerate(output_node.input_nodes):
        nodes_to_ignore = list()
        for y in node_lists:
            if y == i:
                continue
            nodes_to_ignore += node_lists[y]['roots']
        
        try:
            nodes = node_lists[i]['nodes']
        except KeyError:
            # we never collected the nodes because the chain wasnt considered relavent.
            continue
        
        nodes_in_chain = [x for x in nodes if x not in nodes_to_ignore]
        try:
            cd = bw_chain_dimension.calculate_chain_dimension(input_node, nodes_in_chain)
        except bw_chain_dimension.NotInChainError:
            cd = bw_chain_dimension.calculate_chain_dimension(input_node, [input_node])
        
        if cd.width > 96:
            cds.append(cd)
    return cds

def get_node_chain_simple(node: LayoutNode):
    def _populate_chain_simple(node: LayoutNode):
        input_node: LayoutNode
        for input_node in node.input_nodes:
            if input_node.has_branching_outputs:
                continue
            chain.append(input_node)
            _populate_chain_simple(input_node)
    chain = [node]
    _populate_chain_simple(node)
    return chain

def get_node_chain(node: LayoutNode):
    def _populate_chain(node: LayoutNode):
        input_node: LayoutNode
        for input_node in node.input_nodes:
            if input_node.has_branching_outputs:
                roots.append(input_node)
            chain.append(input_node)
            _populate_chain(input_node)
    chain = [node]
    roots = list()
    if node.has_branching_outputs:
        roots.append(node)
    _populate_chain(node)
    return chain, roots
    

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
