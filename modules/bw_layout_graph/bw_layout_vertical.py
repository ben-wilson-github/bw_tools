from typing import Tuple

from common import bw_node
from common import bw_node_selection
from common import bw_chain_dimension


SPACER = 32

def calculate_chain_dimension2(node: bw_node.Node):
    cd = bw_chain_dimension.ChainDimension(
        max_x=node.position.x + (node.width / 2),
        min_x=node.position.x - (node.width / 2),
        max_y=node.position.y + (node.height / 2),
        min_y=node.position.y - (node.height / 2)
    )
    node.chain_dimension = cd

    if not node.has_branching_outputs:
        for input_node in node.input_nodes:
            if input_node.chain_dimension is None:
                continue

            cd.min_x = min(input_node.chain_dimension.min_x, cd.min_x)
            cd.min_y = min(input_node.chain_dimension.min_y, cd.min_y)
            cd.max_y = max(input_node.chain_dimension.max_y, cd.max_y)

    for output_node in node.output_nodes:
        calculate_chain_dimension2(output_node)


def build_downstream_data(node_selection: bw_node_selection.NodeSelection):
    for node in node_selection.end_nodes:
        calculate_chain_dimension2(node)


def update_chain_positions(node, offset, seen):
    if node not in seen:
        node.set_position(node.position.x, node.position.y + offset)
        seen.append(node)

    for input_node in node.input_nodes:
        update_chain_positions(input_node, offset, seen)


def get_node_furthest_back(nodes: Tuple[bw_node.Node, ...]) -> bw_node.Node:
    for i, node in enumerate(nodes):
        if i == 0:
            continue
        previous_node = nodes[i - 1]
        if node.chain_dimension.min_x > previous_node.chain_dimension.min_x:
            return previous_node
        elif node.position.x == previous_node.position.x:
            continue
        else:
            return node
    return nodes[0]


def move_nodes_below_sibling_above(sorted_branching_nodes: Tuple[bw_node.Node, ...],
                                   node_selection: bw_node_selection.NodeSelection):
    # move all children down
    for node in sorted_branching_nodes:
        for i, input_node in enumerate(node.input_nodes):
            if i == 0:
                continue

            # Must update the chain dimensions after each move
            # because the graph is changing
            build_downstream_data(node_selection)

            input_node_above = node.input_nodes[i - 1]

            old_y = input_node.position.y
            new_y = input_node_above.chain_dimension.max_y + (input_node.height / 2) + SPACER
            offset = new_y - old_y

            seen = []
            update_chain_positions(input_node, offset, seen)


def realign_nodes(sorted_branching_nodes: Tuple[bw_node.Node, ...],
                  node_selection: bw_node_selection.NodeSelection):
    for node in sorted_branching_nodes:
        build_downstream_data(node_selection)

        sorted_by_min_x = sorted(
            list(node.input_nodes),
            key=lambda item: item.chain_dimension.min_x
        )
        input_node_furthest_back = get_node_furthest_back(tuple(sorted_by_min_x))

        offset = node.position.y - input_node_furthest_back.position.y

        seen = [node]
        update_chain_positions(node, offset, seen)


def run(node_selection: bw_node_selection.NodeSelection):
    sorted_branching_nodes = tuple(sorted(
        list(node_selection.input_branching_nodes),
        key=lambda item: item.position.x))

    move_nodes_below_sibling_above(sorted_branching_nodes, node_selection)
    realign_nodes(sorted_branching_nodes, node_selection)

    # rebuilding the chain dimnesions every loop is too
    # not slow. Can probably only build the hain for the siblin above when nedded instead.
    #
    # Next step would be to average teh positions after if they are too few
    # But first, we should try to solve main line idea before offseting in y
    # because branching close to the root are positions below the siblings entire
    # tree, even if that sibling was a mainline and further back.

    # maybe we should average the node positions after
    # Down again
    for node in sorted_branching_nodes:
        if not node.has_input_nodes_connected:
            continue

        build_downstream_data(node_selection)
        for i, input_node in enumerate(node.input_nodes):
            if i == 0:
                continue

            top_of_chain = input_node.chain_dimension.min_y
            bottom_of_previous_chain = node.input_nodes[i - 1].chain_dimension.max_y
            offset = bottom_of_previous_chain - top_of_chain

            seen = []
            update_chain_positions(input_node, offset, seen)






