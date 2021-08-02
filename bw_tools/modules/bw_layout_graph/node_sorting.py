from typing import List
from enum import IntEnum

from bw_tools.common.bw_node import Node

from .alignment_behavior import (AverageToOutputsYAxis, NodeAlignmentBehavior,
                                 StaticAlignment)

SPACER = 32


def run_sort(node: Node, already_processed: List[Node]):
    for input_node in node.input_nodes:
        process_node(input_node, node, already_processed)
        run_sort(input_node, already_processed)


def process_node(node: Node, output_node: Node, already_processed: List[Node]):
    offset = get_offset_value(node, node.closest_output_node_in_x)
    node.set_position(node.closest_output_node_in_x.pos.x - offset,
                      node.closest_output_node_in_x.pos.y)

    if node not in already_processed:
        behavior = calculate_behavior(node)
        node.alignment_behavior = behavior
        already_processed.append(node)

    node.alignment_behavior.setup(output_node)


def get_offset_value(node: Node, output_node: Node) -> float:
    if node.is_root:
        spacer = SPACER * 4
    else:
        spacer = SPACER
    half_output = output_node.width / 2
    half_input = node.width / 2
    return half_output + spacer + half_input





def calculate_behavior(node: Node) -> NodeAlignmentBehavior:
    if not node.is_root:
        return StaticAlignment()
    
    if node.chain_contains_another_root():
        return StaticAlignment()

    # Find branching output nodes
    # for all output nodes, does one have a chain which connect to myself
        # no = Average
        # yes
            # branch inbetween?
                # no = Static
                # yes
                    # for all the branches inbetween, does one connect to another root
                        # yes = Static
                        # no
                            # Does output node have 3 or more inputs
                                # yes = average
                                #  no = static
        
           

    # One of the output nodes inputs routes back to myself 
    # And there are no other loops involved. None of the outputs inputs contain another root = Static
    # under the index

    

    for output_node in node.output_nodes:
        indices = node.indices_in_output(output_node)
        if not output_node.find_node_in_chain(node, skip_indices=indices):
            return AverageToOutputsYAxis()
    return StaticAlignment()


    # for output_node in node.output_nodes:
    #     indices = node.indices_in_output(output_node)

    #     # One of my outputs inputs are going to expand, ignoring the chain I came from
    #     if output_node.chain_contains_branching_inputs(skip_indices=indices):
    #         return StaticAlignment()

    # for output_node in node.output_nodes:
    #     indices = node.indices_in_output(output_node)

    #     # One of my outputs inputs doesnt have another root (exlcude myself)
    #     if output_node.chain_contains_another_root(skip_indices=indices, skip_nodes=[node]):
    #         return AverageToOutputsYAxis()

    return StaticAlignment()
