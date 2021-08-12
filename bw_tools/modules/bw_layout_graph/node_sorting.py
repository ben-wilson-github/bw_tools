from bw_tools.common.bw_node import Float2
from .alignment_behavior import NodeAlignmentBehavior, StaticAlignment
from .layout_node import LayoutNode
from bw_tools.modules.bw_layout_graph import layout_node
from bw_tools.common import bw_chain_dimension
from . import aligner
from typing import List

SPACER = 32

# loop through each branching node (it needs to be sorted in x, up to down)
    # find the mainline node
    # Find the longest sibling chain, excluding the nodes from the mainline
    # set its offset to new position, if it farther back then the current position. (it might be a root)
    # if the y parent shoudl change, update offset
    # then reposition node

# def reposition node(node)
    # If the node is a normal node
        # then position it to the offset parent
        # for each input in the node
            # reposition node
    # else if the node is a root node
        # then position it to the closet parent
        # then position to farthest y parent
        # update the offset always, because the y parent might have moved forward
        # for each input in the node
            # reposition node
    # if the node is a branching input node,
        # then find the mainline node (its the one most left)
        # call reposition node with all children except the mainline, setting a fresh bound value, returning with new left bound
            # store bound for index
        # get the most left bound
        # then move the mainline to either the new left bound, or the closest parent. Which ever is farther back
        # call reposition node with mainline node

    # take min left bound
    # return left bound

# Mainline logic
# Find mainline node = the input node which is farthest away, otherwise the one with the longest chain
# longest chain is the one farthest back, ignoring all nodes in the siblings

# while moved is true
    # loop through each branching input
        # move mainline node back
            # only if the new position would actually move it back.
            # The left bound to move back too needs to be the longest chain on consecuative nodes
            # or if not consecuative, its including branching output nodes only if the incoming parent is the closest parent in x
            # otherwise its likely to be far away and will look visually weird
        # update offset
        # reposition all input nodes
            # if branching outputs, then move to closest x and update offset

def get_mainline_node(cds: List[bw_chain_dimension.ChainDimension]):
    
    previous_bound = cds[0].bounds.left
    for i, cd in enumerate(cds[1:]):
        if cd.bounds.left != previous_bound:
            remaining_cds = cds[:i+1]
            remaining_cds.sort(key=lambda x: x.node_count)
            remaining_cds.reverse()
            return remaining_cds[0].right_node
    return cds[0].right_node


def run_mainline(branching_nodes: List[LayoutNode], branching_output_nodes: List[LayoutNode]):
    branching_nodes.sort(key=lambda node: node.pos.x)
    # branching_nodes.reverse()
    print(len(branching_nodes))

    moved = True
    first_time = False
    data = dict()

    i = 0
    for j in range(2):
        moved = False
        for branching_node in branching_nodes:
            print('============')
            print(branching_node)
            print(branching_node.input_nodes)
            i += 1
            if i == 7:
                print('as')
            if branching_node.identifier == 1420168050:
                print('ass')

            cds: List[bw_chain_dimension.ChainDimension] = get_unique_chain_dimensions(branching_node, first_time, data)
            print(cds)
            if len(cds) >= 2:
                cds.sort(key=lambda x: x.bounds.left)
                mainline_node: LayoutNode = get_mainline_node(cds)

                left_bound = cds[1].bounds.left

                potential_x = left_bound - SPACER - (mainline_node.width / 2)
                if potential_x < mainline_node.pos.x:
                    old_pos = mainline_node.pos
                    mainline_node.set_position(potential_x, mainline_node.pos.y)
                    # if mainline_node.pos.x != old_pos.x:
                    #     moved = True
                

                    mainline_node.alignment_behavior.update_offset(mainline_node.pos)
                    # if i == 4:
                    #     return

                    for input_node in mainline_node.input_nodes:
                        reposition_node(input_node, chain_left_bound=input_node.pos.x)
                    
                    # Must update the offsets after the entire network has been updated
                    # Not possible to do it as we go
                    for branching_output_node in branching_output_nodes:
                        branching_output_node.alignment_behavior.offset_node = branching_output_node.farthest_output_nodes_in_x[0]
                        branching_output_node.alignment_behavior.update_offset(branching_output_node.pos)
                        # branching_output_node.alignment_behavior.exec()
            
    
            # if i == 7:
            #     raise ArithmeticError()
            #     print('as')
    # if first_time:
        #     first_time = False
        # else:
        #     first_time = True

def reposition_node(node: LayoutNode, chain_left_bound):
    if node.identifier == 1420934573:
        print('a')
    if node.has_branching_outputs:
        node.alignment_behavior.exec()
        potential_new_x = node.closest_output_node_in_x.pos.x - (node.closest_output_node_in_x.width / 2) - SPACER - (node.width / 2)
        node.set_position(potential_new_x, node.pos.y)

        # node.alignment_behavior.offset_node = node.farthest_output_nodes_in_x[0]
        # node.alignment_behavior.update_offset(node.pos)
        for input_node in node.input_nodes:
            result_left_bound = reposition_node(input_node, chain_left_bound=input_node.pos.x)
            chain_left_bound = min(result_left_bound, node.pos.x)

    
    # elif node.has_branching_inputs:
    #     node.alignment_behavior.exec()
    #     inputs = list(node.input_nodes)
    #     inputs.sort(key=lambda node: node.pos.x)
    #     mainline_node: LayoutNode = inputs[0]
    #     for input_node in inputs[1:]:
    #         result_left_bound = reposition_node(input_node, chain_left_bound=input_node.pos.x)
    #         chain_left_bound = min(result_left_bound, node.pos.x)
        
    #     new_x = min(chain_left_bound, mainline_node.closest_output_node_in_x.pos.x)
    #     mainline_node.set_position(new_x - (mainline_node.width / 2) - SPACER, mainline_node.pos.y)
    #     mainline_node.alignment_behavior.update_offset(mainline_node.pos)
    #     for input_node in mainline_node.input_nodes:
    #         result_left_bound = reposition_node(input_node, chain_left_bound=input_node.pos.x)
    #         chain_left_bound = min(result_left_bound, node.pos.x)
    
    else:   # normal node
        node.alignment_behavior.exec()
        for input_node in node.input_nodes:
            result_left_bound = reposition_node(input_node, chain_left_bound=input_node.pos.x)
            chain_left_bound = min(result_left_bound, node.pos.x)
    
    chain_left_bound = min(chain_left_bound, node.pos.x - (node.width / 2))
    return chain_left_bound

    

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
    if output_node.identifier == 1:
        print('a')


    cds: List[bw_chain_dimension.ChainDimension] = get_unique_chain_dimensions(output_node)
    cds.sort(key=lambda x: x.bounds.left)
    print(cds)
    print('==========')
    if len(cds) >= 2:
        mainline_node: LayoutNode = cds[0].right_node
        mainline_node.set_position(
            cds[1].bounds.left - SPACER - (mainline_node.width / 2),
            mainline_node.farthest_output_nodes_in_x[0].pos.y
        )
        if output_node.identifier == 1419826112:
            print('a')
            # raise ArithmeticError()

        mainline_node.alignment_behavior.update_offset(mainline_node.pos)
        mainline_node.update_all_chain_positions_deep()
        if output_node.identifier == 1:
            raise ArithmeticError()

    if output_node.identifier == 1:
        raise ArithmeticError()
    

def get_chain_dimensions2(output_node: LayoutNode):
    cds = list()
    input_node: LayoutNode
    for input_node in output_node.input_nodes:
        if input_node.has_branching_outputs:
            continue
        node_list = get_node_chain_simple(input_node)
        cds.append(bw_chain_dimension.calculate_chain_dimension(input_node, node_list))
    return cds

def get_unique_chain_dimensions(output_node: LayoutNode, first: bool, data: dict):
    node_lists = dict()
    input_node: LayoutNode
    if output_node.identifier == 1420042473:
        print('a')
    for i, input_node in enumerate(output_node.input_nodes):
        # if input_node.alignment_behavior.offset_node is not output_node:
        #     continue
        node_lists[i] = dict()

        if first:
            node_list, roots_in_chain = get_every_input_node(input_node)
        else:
            node_list, roots_in_chain = get_every_input_node2(input_node)
            # node_list = get_node_chain_simple(input_node)
            # node_list = aligner.calculate_node_list(input_node, [])
            # node_list, _ = get_every_input_node(input_node)
            roots_in_chain = []
        node_lists[i]['nodes'] = node_list
        node_lists[i]['roots'] = roots_in_chain
    
    if len(node_lists) < 2:
        return []
    
    if output_node.identifier == 1420042473:
        print('a')
    
    cds: List[bw_chain_dimension.ChainDimension] = list()
    for i, input_node in enumerate(output_node.input_nodes):
        nodes_to_ignore = list()
        for y in node_lists:
            if y == i:
                continue
            for n in node_lists[y]['nodes']:
                if n not in nodes_to_ignore:
                    nodes_to_ignore.append(n)
        
        if input_node in nodes_to_ignore:
            nodes_to_ignore.remove(input_node)
        

        nodes = node_lists[i]['nodes']
        
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
        
        if cd.width > 96:
            cds.append(cd)
        # cds.append(cd)
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
    if not node.has_branching_outputs:
        _populate_chain_simple(node)
    return chain

def get_every_input_node2(node: LayoutNode):
    def _populate_chain(node: LayoutNode):
        input_node: LayoutNode
        for input_node in node.input_nodes:
            if input_node.pos.x < node.pos.x - (node.width / 2) - SPACER - (input_node.width / 2) and input_node is not node.alignment_behavior.offset_node:
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
    return chain, roots

def get_every_input_node(node: LayoutNode):
    def _populate_chain(node: LayoutNode):
        input_node: LayoutNode
        for input_node in node.input_nodes:
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
