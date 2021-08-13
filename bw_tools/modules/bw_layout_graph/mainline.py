from __future__ import annotations
from typing import TYPE_CHECKING, List
from bw_tools.common import bw_chain_dimension
if TYPE_CHECKING:
    from .layout_node import LayoutNode

ITERATIONS = 1
MIN_CHAIN_SIZE = 64
SPACER = 32

LAST NODE IN CHAIN 10 not working again
def run_mainline(branching_nodes: List[LayoutNode], branching_output_nodes: List[LayoutNode]):
    branching_nodes.sort(key=lambda node: node.pos.x)
    i = 0 
    # return
    for _ in range(ITERATIONS):
        for branching_node in branching_nodes:
            i += 1
            print('============')
            print(branching_node)
            print(branching_node.input_nodes)
            if branching_node.identifier == 1420227968:
                print('as')
            cds: List[bw_chain_dimension.ChainDimension] = get_chain_dimensions(branching_node)

            # For pleasing visual, do not consider chains
            # which are very small.
            [cds.remove(cd) for cd in cds if cd.width <= MIN_CHAIN_SIZE or branching_node is not cd.right_node.farthest_output_nodes_in_x[0]]

            if len(cds) < 2:   # Only need to do work if there are 2 or more
                continue

            cds.sort(key=lambda x: x.bounds.left)
            mainline_node: LayoutNode = get_mainline_node(cds)
            
            left_bound = cds[1].bounds.left
            left_bound_node = cds[1].left_node
            right_node: LayoutNode = cds[1].right_node
            offset = right_node.farthest_output_nodes_in_x[0].pos.x - right_node.pos.x
            print(offset)
            if offset > 128:
                continue
                left_bound = branching_node.pos.x - (branching_node.width / 2)# - SPACER - (right_node.width / 2)

            potential_x = left_bound - SPACER - (mainline_node.width / 2)
            if potential_x > mainline_node.pos.x:
                continue

            mainline_node.set_position(potential_x, mainline_node.pos.y)
            mainline_node.alignment_behavior.offset_node = left_bound_node
            mainline_node.alignment_behavior.update_offset(mainline_node.pos)
            reposition_node(mainline_node, chain_left_bound=mainline_node.pos.x)

            # # Must update the offset values after the entire network has been updated.
            # # Not possible to do it as we go as we need the entire network solved
            # for branching_output_node in branching_output_nodes:
            #     branching_output_node.alignment_behavior.offset_node = branching_output_node.farthest_output_nodes_in_x[0]
            #     branching_output_node.alignment_behavior.update_offset(branching_output_node.pos)
            
            if i == -1:
                raise ArithmeticError()

        # for branching_node in branching_nodes:
        #     mainline_node = branching_node.input_nodes[0]
        #     for input_node in branching_node.input_nodes:
        #         if input_node.pos.x < mainline_node.pos.x:
        #             mainline_node = input_node
            
        #     cds: List[bw_chain_dimension.ChainDimension] = get_chain_dimensions(branching_node)
            


def move_mainline_chain(mainline_node: LayoutNode, new_x: float):
    # recursively update inputs
    for input_node in mainline_node.input_nodes:
        reposition_node(input_node, chain_left_bound=input_node.pos.x)

def calculate_node_lists(output_node: LayoutNode) -> List[List[LayoutNode]]:
    """Builds a list of every node in a chain"""
    node_lists = list()
    input_node: LayoutNode
    for input_node in output_node.input_nodes:
        node_lists.append(get_every_input_node2(input_node))
    return node_lists

def prune_node_list_by_sibling_chains(input_node: LayoutNode, index: int, node_lists: List[List[LayoutNode]]):
    for y in range(len(node_lists)):
        if y == index:
            continue
        [node_lists[index].remove(node) for node in node_lists[y] if node in node_lists[index] and node is not input_node]



def get_chain_dimensions(output_node: LayoutNode):
    """
    Returns a chain dimension for the input nodes of a given node of only
    the unique nodes in that chain. That is, any node which is present in one or
    more input chains, will not be included.
    """
    node_lists = calculate_node_lists(output_node)
    if len(node_lists) < 2:
        return []

    cds: List[bw_chain_dimension.ChainDimension] = list()
    # for i, input_node in enumerate(output_node.input_nodes):
    # #     prune_node_list_by_sibling_chains(input_node, i, node_lists)
    #     try:
    #         cd = bw_chain_dimension.calculate_chain_dimension(input_node, node_lists[i])
    #     except bw_chain_dimension.NotInChainError:
    #         cd = bw_chain_dimension.calculate_chain_dimension(input_node, [input_node])

    for i, input_node in enumerate(output_node.input_nodes):
        nodes_to_ignore = list()
        for y, _ in enumerate(node_lists):
            if y == i:
                continue
            for n in node_lists[y]:
                if n not in nodes_to_ignore:
                    nodes_to_ignore.append(n)
        
        if input_node in nodes_to_ignore:
            nodes_to_ignore.remove(input_node)
        

        nodes = node_lists[i]
        
        if output_node.identifier == 1420042473:
            print('f')
        nodes_in_chain = list()
        for n in nodes:
            if n not in nodes_to_ignore and n not in nodes_in_chain:
                nodes_in_chain.append(n)

        try:
            cd = bw_chain_dimension.calculate_chain_dimension(input_node, nodes_in_chain)
        except bw_chain_dimension.NotInChainError:
            cd = bw_chain_dimension.calculate_chain_dimension(input_node, [input_node])
        
        
        cds.append(cd)
    return cds

def get_mainline_node(cds: List[bw_chain_dimension.ChainDimension]):
    
    previous_bound = cds[0].bounds.left
    for i, cd in enumerate(cds[1:]):
        if cd.bounds.left != previous_bound:
            remaining_cds = cds[:i+1]
            remaining_cds.sort(key=lambda x: x.node_count)
            remaining_cds.reverse()
            return remaining_cds[0].right_node
    return cds[0].right_node

def reposition_node(node: LayoutNode, chain_left_bound):
    if node.identifier == 1420934573:
        print('a')
    if node.has_branching_outputs:
        # node.alignment_behavior.exec()
        potential_new_x = node.closest_output_node_in_x.pos.x - (node.closest_output_node_in_x.width / 2) - SPACER - (node.width / 2)
        # if potential_new_x < node.pos.x:
        node.set_position(potential_new_x, node.pos.y)

        # node.alignment_behavior.offset_node = node.farthest_output_nodes_in_x[0]
        # node.alignment_behavior.update_offset(node.pos)
        for input_node in node.input_nodes:
            result_left_bound = reposition_node(input_node, chain_left_bound=input_node.pos.x)
            chain_left_bound = min(result_left_bound, node.pos.x)

    
    elif node.has_branching_inputs:
        node.alignment_behavior.exec()
        mainline_node = node.input_nodes[0]
        for input_node in node.input_nodes:
            if input_node.pos.x < mainline_node.pos.x:
                mainline_node = input_node
        
        for input_node in node.input_nodes:
            if input_node is mainline_node:
                continue
            reposition_node(input_node, chain_left_bound=input_node.pos.x)
        
        mainline_node.alignment_behavior.exec()
        for input_node in mainline_node.input_nodes:
            reposition_node(mainline_node, chain_left_bound=mainline_node.pos.x)

    
    else:   # normal node
        node.alignment_behavior.exec()
        for input_node in node.input_nodes:
            result_left_bound = reposition_node(input_node, chain_left_bound=input_node.pos.x)
            chain_left_bound = min(result_left_bound, node.pos.x)
    
    chain_left_bound = min(chain_left_bound, node.pos.x - (node.width / 2))
    return chain_left_bound

def get_every_input_node2(node: LayoutNode):
    def _populate_chain(node: LayoutNode):
        input_node: LayoutNode
        for input_node in node.input_nodes:
            # if input_node.pos.x < node.pos.x - (node.width / 2) - SPACER - (input_node.width / 2) # and node is not input_node.farthest_output_nodes_in_x[0]:
            #     continue
            if input_node.has_branching_outputs:
                continue
            if input_node.has_branching_outputs and input_node not in roots:
                roots.append(input_node)
            if input_node not in chain:
                chain.append(input_node)
            _populate_chain(input_node)
    chain = [node]
    roots = list()
    if node.has_branching_outputs and node not in roots:
        roots.append(node)
    _populate_chain(node)
    return chain