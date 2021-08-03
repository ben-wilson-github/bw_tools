from dataclasses import dataclass, field
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

@dataclass
class Route:
    root_node: Node
    target_node: Node
    index: int
    branching_nodes: List[Node] = field(init=False, default_factory=list)


def calculate_behavior(node: Node) -> NodeAlignmentBehavior:
    if not node.is_root:
        return StaticAlignment()

    if node.chain_contains_a_root(None):
        return StaticAlignment()

    # Find branching output nodes
    # 0 branching outputs = Average
    # Multiple branching outputs = Static
    # 1 Branching output
        # Does one of the routes connect to myself?
            # no = average
            # yes - Does the one remaining output node have 3 or more inputs?
                # no = Static
                # yes
                    # collect all the branching nodes inbtween the output and root for each route
                    # branch inbetween?
                        # no = Average
                        # yes
                            # for all the branches inbetween, does one of the branch ndoes connect to another root
                                # yes = Static
                                # no = Average

    # For all branching output nodes and their routes
    Branching_output_nodes: List[Node] = list()
    for output_node in node.output_nodes:
        if not output_node.has_branching_inputs:
            continue
        Branching_output_nodes.append(output_node)
        

    # There are no branching nodes
    if len(Branching_output_nodes) == 0:   
        return AverageToOutputsYAxis()
    # There are multiple branching output nodes
    elif len(Branching_output_nodes) > 1:
        return StaticAlignment()
    
    # There is only 1 branching output node now
    output_node = Branching_output_nodes[0]
    # Do any of the routes lead back to myself?
    indices = node.indices_in_output(output_node)
    routes = output_node.find_routes_to_node(node, skip_indices=indices)
    if len(routes) == 0:
        return AverageToOutputsYAxis()

    # Does the otuput node have 3 or more inputs?
    if output_node.input_node_count < 3:
        return StaticAlignment()

    branching_nodes_in_routes: List[Node] = list()
    for route in routes:
        branching_nodes_in_routes += route.branching_nodes
    # Are there any branching nodes between the output and the root node?
    if len(branching_nodes_in_routes) == 0:
        AverageToOutputsYAxis()

    # Does one of the branching nodes connect to another root?
    if any(branch.chain_contains_a_root(root_to_ignore=node) for branch in branching_nodes_in_routes):
        return StaticAlignment()
    else:
        return AverageToOutputsYAxis()
