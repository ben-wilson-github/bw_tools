from __future__ import annotations
from typing import TYPE_CHECKING, List
from operator import attrgetter
from bw_tools.common import bw_chain_dimension
if TYPE_CHECKING:
    from .layout_node import LayoutNode

MIN_CHAIN_SIZE = 96
SPACER = 32


def run_mainline(branching_nodes: List[LayoutNode], branching_output_nodes: List[LayoutNode]):
    branching_nodes.sort(key=lambda node: node.pos.x)
    branching_node: LayoutNode
    for branching_node in branching_nodes:
        push_back_mainline_ignoring_branching_output_nodes(branching_node)

    # TODO: make this an option too
    branching_output_nodes.sort(key=lambda node: node.pos.x)
    branching_output_nodes.reverse()
    k = 0
    for branching_output_node in branching_output_nodes:
        if k == -1:
            raise ArithmeticError()
        k += 1
        # The idea is to find the largest chain to movew behind for each branching output node
        
        # So find the branching input nodes
        branching_input_nodes = [n for n in branching_output_node.output_nodes if n.has_branching_inputs]
        if len(branching_input_nodes) == 0:
            continue


        # find the longest chain from those branches
        if len(branching_input_nodes) > 0:
            left_most_bound = branching_output_node.farthest_output_nodes_in_x[0].pos.x
            branching_input: LayoutNode
            for branching_input in branching_input_nodes:
                inputs = list(branching_input.input_nodes)
                inputs.remove(branching_output_node)
                cds = get_chain_dimensions_ignoring_branches_return_empty_list(inputs)
                if len(cds) > 0:
                    cds.sort(key=lambda cd: cd.bounds.left)
                    longest_chain = cds[0]
                    left_most_bound = min(left_most_bound, longest_chain.bounds.left)
            
            # for branching_input_node in branching_input_nodes:
            #     inputs = [n for n in branching_input_node.input_nodes if n is not branching_output_node]
            #     cds = get_chain_dimensions_ignoring_branches_return_empty_list(inputs)
            #     if len(cds)
        
            # position the branching output node behind longest chain
            if branching_output_node.pos.x > (left_most_bound - SPACER - branching_output_node.width / 2):
                branching_output_node.set_position(left_most_bound - SPACER - branching_output_node.width / 2,  branching_output_node.farthest_output_nodes_in_x[0].pos.y)
                branching_output_node.alignment_behavior.offset_node = branching_output_node.farthest_output_nodes_in_x[0]
                branching_output_node.alignment_behavior.update_offset(branching_output_node.pos)
                if k == -1:
                    raise ArithmeticError()
                reposition_node(branching_output_node, chain_left_bound=branching_output_node.pos.x, ignore_first=True)

def push_back_mainline_ignoring_branching_output_nodes(branching_node: LayoutNode):
    mainline_node = find_mainline_node(branching_node)

    if mainline_node.has_branching_outputs: # These are handled in pass 2
        return

    inputs = [n for n in branching_node.input_nodes if n is not mainline_node]
    left_bound = find_left_most_bound(inputs)

    mainline_node.set_position(left_bound - SPACER - (mainline_node.width / 2), mainline_node.pos.y)
    mainline_node.alignment_behavior.offset_node = mainline_node.farthest_output_nodes_in_x[0]
    mainline_node.alignment_behavior.update_offset(mainline_node.pos)
    reposition_node(mainline_node, chain_left_bound=mainline_node.pos.x)

def find_left_most_bound(node_list: List[LayoutNode]):
    cds = get_chain_dimensions_ignoring_branches(node_list)
    cd: bw_chain_dimension.ChainDimension = min(cds, key=attrgetter('bounds.left'))
    return cd.bounds.left

def find_potential_mainline_nodes(node: LayoutNode) -> List[LayoutNode]:
    potential_nodes: List[LayoutNode] = list()
    
    # Limit the list to branching nodes if possible
    potential_nodes = [n for n in node.input_nodes if n.has_branching_outputs]
    if not potential_nodes:
        potential_nodes = list(node.input_nodes)

    min_node = min(potential_nodes, key=attrgetter('pos.x'))
    potential_nodes = [n for n in potential_nodes if n.pos.x == min_node.pos.x]
    return potential_nodes

def find_mainline_node(node: LayoutNode):
    potential_mainline_nodes = find_potential_mainline_nodes(node)
    if len(potential_mainline_nodes) == 1:
        return potential_mainline_nodes[0]

    cds: List[bw_chain_dimension.ChainDimension] = get_chain_dimensions_full_chain(node)

    # # For pleasing visual, do not consider chains
    # # which are very small.
    # [cds.remove(cd) for cd in cds if cd.width <= MIN_CHAIN_SIZE and branching_node is not cd.right_node.farthest_output_nodes_in_x[0]]

    min_cd = min(cds, key=attrgetter('bounds.left'))

    chains_of_same_size = [cd for cd in cds if cd.bounds.left == min_cd.bounds.left]
    # TODO: turn into setting maybe between min and max? Bias small or large networks
    mainline_chain = min(chains_of_same_size, key=attrgetter('node_count'))

    return mainline_chain.right_node
   
def get_chain_dimensions_ignoring_branches(nodes: List[LayoutNode]):
    cds = list()
    for node in nodes:
        # node_list = get_every_input_node_ignoring_branches(node)
        node_list = get_every_input_node_ignoring_branches_return_empty_list(node)
        cd = bw_chain_dimension.calculate_chain_dimension(node, node_list)
        cds.append(cd)
    return cds

def get_chain_dimensions_ignoring_branches_return_empty_list(nodes: List[LayoutNode]):
    cds = list()
    for node in nodes:
        node_list = get_every_input_node_ignoring_branches_return_empty_list(node)
        try:
            cd = bw_chain_dimension.calculate_chain_dimension(node, node_list)
        except bw_chain_dimension.NotInChainError:
            continue
        cds.append(cd)
    return cds

def move_mainline_chain(mainline_node: LayoutNode, new_x: float):
    # recursively update inputs
    for input_node in mainline_node.input_nodes:
        reposition_node(input_node, chain_left_bound=input_node.pos.x)

def calculate_node_lists_ignoring_branches(output_node: LayoutNode) -> List[List[LayoutNode]]:
    """Builds a list of every node in a chain"""
    node_lists = list()
    input_node: LayoutNode
    for input_node in output_node.input_nodes:
        node_lists.append(get_every_input_node_ignoring_branches(input_node))
    return node_lists

def calculate_node_lists_for_everything(output_node: LayoutNode) -> List[List[LayoutNode]]:
    """Builds a list of every node in a chain"""
    node_lists = list()
    input_node: LayoutNode
    for input_node in output_node.input_nodes:
        node_lists.append(get_every_input_node_everything(input_node))
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
    node_lists = calculate_node_lists_ignoring_branches(output_node)
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

def get_chain_dimensions_full_chain(output_node: LayoutNode):
    node_lists = calculate_node_lists_for_everything(output_node)
    if len(node_lists) < 2:
        return []

    cds = list()
    for i, input_node in enumerate(output_node.input_nodes):
        cd = bw_chain_dimension.calculate_chain_dimension(input_node, node_lists[i])
        cds.append(cd)
    return cds

def get_mainline_node_from_left_most_bound(cds: List[bw_chain_dimension.ChainDimension]):
    previous_bound = cds[0].bounds.left
    for i, cd in enumerate(cds[1:]):
        if cd.bounds.left != previous_bound:
            remaining_cds = cds[:i+1]
            remaining_cds.sort(key=lambda x: x.node_count)
            remaining_cds.reverse()
            return remaining_cds[0].right_node
    return cds[0].right_node

def reposition_node(node: LayoutNode, chain_left_bound, ignore_first=False):
    if node.identifier == 1420934573:
        print('a')
    inputs = list()
    node.alignment_behavior.exec()
    inputs = list(node.input_nodes)
    if node.has_branching_outputs and not ignore_first:
        # node.alignment_behavior.exec()
        potential_new_x = node.closest_output_node_in_x.pos.x - (node.closest_output_node_in_x.width / 2) - SPACER - (node.width / 2)
        # if potential_new_x < node.pos.x:
        node.set_position(potential_new_x, node.pos.y)

        node.alignment_behavior.offset_node = node.farthest_output_nodes_in_x[0]
        node.alignment_behavior.update_offset(node.pos)

    if node.has_branching_inputs:
        node.alignment_behavior.exec()
        mainline_node = node.input_nodes[0]
        for input_node in node.input_nodes:
            if input_node.pos.x < mainline_node.pos.x:
                mainline_node = input_node
        
        for input_node in node.input_nodes:
            if input_node is mainline_node:
                continue
            inputs.append(input_node)
        inputs.append(mainline_node)
        
        mainline_node.alignment_behavior.exec()


    for input_node in inputs:
        reposition_node(input_node, chain_left_bound=input_node.pos.x)
    
    chain_left_bound = min(chain_left_bound, node.pos.x - (node.width / 2))
    return chain_left_bound

def get_every_input_node_ignoring_branches(node: LayoutNode):
    def _populate_chain(node: LayoutNode):
        input_node: LayoutNode
        for input_node in node.input_nodes:
            if input_node.has_branching_outputs:
                continue
            if input_node not in chain:
                chain.append(input_node)
            _populate_chain(input_node)
    chain = [node]
    _populate_chain(node)
    return chain

def get_every_input_node_ignoring_branches_return_empty_list(node: LayoutNode):
    def _populate_chain(node: LayoutNode):
        input_node: LayoutNode
        for input_node in node.input_nodes:
            if input_node.has_branching_outputs:
                continue
            if input_node not in chain:
                chain.append(input_node)
            _populate_chain(input_node)
    if node.has_branching_outputs:
        return []
    chain = [node]
    _populate_chain(node)
    return chain

def get_every_input_node_everything(node: LayoutNode):
    def _populate_chain(node: LayoutNode):
        input_node: LayoutNode
        for input_node in node.input_nodes:
            # if input_node.pos.x < node.pos.x - (node.width / 2) - SPACER - (input_node.width / 2) # and node is not input_node.farthest_output_nodes_in_x[0]:
            #     continue
            # if input_node.has_branching_outputs:
            #     continue
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