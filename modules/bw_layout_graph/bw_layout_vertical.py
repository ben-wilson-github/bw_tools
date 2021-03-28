from common import bw_node
from common import bw_node_selection
from common import bw_chain_dimension


def calculate_chain_dimension(node: bw_node.Node):
    chain_dimension = bw_chain_dimension.ChainDimension(
        max_x=node.position.x + (node.width / 2),
        min_x=node.position.x - (node.width / 2),
        max_y=node.position.y + (node.height / 2),
        min_y=node.position.y - (node.height / 2)
    )
    chain_dimension.end_node = node
    node.chain_dimension = chain_dimension

    for input_node in node.input_nodes:
        if input_node.chain_dimension is not None and not input_node.has_branching_outputs:
            # if input_node.chain_dimension.min_x < chain_dimension.min_x:
            #     chain_dimension.min_x = input_node.chain_dimension.min_x
            #     chain_dimension.end_node = input_node.chain_dimension.end_node
            chain_dimension.min_x = min(input_node.chain_dimension.min_x, chain_dimension.min_x)
            chain_dimension.min_y = min(input_node.chain_dimension.min_y, chain_dimension.min_y)
            chain_dimension.max_y = max(input_node.chain_dimension.max_y, chain_dimension.max_y)

    for output_node in node.output_nodes:
        calculate_chain_dimension(output_node)


def build_downstream_data(node_selection: bw_node_selection.NodeSelection):
    for node in node_selection.end_nodes:
        calculate_chain_dimension(node)


def update_chain_positions(node, offset, seen):
    if node not in seen:
        node.set_position(node.position.x, node.position.y + offset)
        seen.append(node)

    for input_node in node.input_nodes:
        update_chain_positions(input_node, offset, seen)


def run(node_selection: bw_node_selection.NodeSelection):
    Update the calculate chain dimension fcuntion
    Can I include the branching node?
    if I am a branchign node, then create a new dimension
        otherwise take the largest dimensions from inptus

    Need to figure out if there is a better way of doing vertical pass
    I want to place each chain under the other
    then find the mainline and position that to center
    and move everything else up with the same offset

    sorted_branching_nodes = sorted(
        list(node_selection.input_branching_nodes),
        key=lambda item: item.position.x)

    # move all children down
    for node in sorted_branching_nodes:
        if not node.has_input_nodes_connected:
            continue

        build_downstream_data(node_selection)

        for i, input_node in enumerate(node.input_nodes):
            if i == 0:
                continue

            previous_input_node = node.input_nodes[i - 1]
            old_y = input_node.position.y
            new_y = previous_input_node.chain_dimension.max_y + (previous_input_node.height / 2)
            offset = new_y - old_y

            seen = []
            update_chain_positions(input_node, offset, seen)

    # Move back up
    for node in sorted_branching_nodes:
        if not node.has_input_nodes_connected:
            continue

        build_downstream_data(node_selection)
        sorted_by_min_x = sorted(
            list(node.input_nodes),
            key=lambda item: item.chain_dimension.min_x
        )
        offset = sorted_by_min_x[0].position.y - node.position.y

        seen = [node]
        update_chain_positions(node, -offset, seen)

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






