from typing import Tuple
from typing import Union

from common import bw_node
from common import bw_node_selection
from common import bw_chain_dimension

SPACER = 32

def calculate_chain_dimension(node: bw_node.Node):
    cd = bw_chain_dimension.ChainDimension(
        right_bound=node.position.x + (node.width / 2),
        left_bound=node.position.x - (node.width / 2),
        bottom_bound=node.position.y + (node.height / 2),
        top_bound=node.position.y - (node.height / 2)
    )
    node.chain_dimension = cd

    if not node.has_branching_outputs:
        for input_node in node.input_nodes:
            if input_node.chain_dimension is None:
                continue

            cd.left_bound = min(input_node.chain_dimension.min_x, cd.left_bound)
            cd.top_bound = min(input_node.chain_dimension.min_y, cd.top_bound)
            cd.bottom_bound = max(input_node.chain_dimension.max_y, cd.bottom_bound)

    for output_node in node.output_nodes:
        calculate_chain_dimension(output_node)


def build_downstream_data(node_selection: bw_node_selection.NodeSelection):
    for node in node_selection.end_nodes:
        calculate_chain_dimension(node)


def update_inputs_positions(node: bw_node.Node, offset, seen):
    if node in seen:
        return

    node.set_position(node.position.x + offset, node.position.y)
    seen.append(node)

    for input_node in node.input_nodes:
        update_inputs_positions(input_node, offset, seen)


def calculate_mainline(node: bw_node.Node) -> Tuple[Union[bw_node.Node, None], Union[bw_node.Node, None]]:
    sorted_by_min_x = sorted(
        list(node.input_nodes),
        key=lambda item: item.chain_dimension.min_x
    )

    for i, n in enumerate(sorted_by_min_x):
        if i == 0:
            continue
        previous_node = sorted_by_min_x[i - 1]
        if n.chain_dimension.min_x > previous_node.chain_dimension.min_x:
            return previous_node, n
        elif n.position.x == previous_node.position.x:
            continue
        else:
            return n, previous_node
    return None, None


def run(node_selection: bw_node_selection.NodeSelection):
    print('Split nodes into sorted groups of selections')
    print('split by branching nodes')
    # build_downstream_data(node_selection)

    # i = 0
    # sorted_branching_nodes = tuple(sorted(
    #     list(node_selection.input_branching_nodes),
    #     key=lambda item: item.position.x))

    # for node in sorted_branching_nodes:
    #     mainline_node, largest_sibling = calculate_mainline(node)
    #     if mainline_node is None:
    #         continue

    #     # To calculate the offset, we should extend the dimension to include
    #     # the mainline node
    #     # offset_dimension = largest_sibling.chain_dimension.min_x - (mainline_node.width / 2) - SPACER
    #     offset_dimension = largest_sibling.chain_dimension.min_x
    #     offset = offset_dimension - mainline_node.position.x
    #     print(offset)
    #     threshold = (mainline_node.width / 2) + SPACER
    #     print(threshold)

    #     if offset < -((mainline_node.width / 2) + SPACER):
    #         seen = []
    #         update_inputs_positions(mainline_node, -offset, seen)



    #     # if i == 1:
        #     return
        # i += 1
        # print(node.chain_dimension)
        # sorted_inputs = sorted(list(node.input_nodes), key=lambda item: item.chain_dimension.min_x)
        # furthest_input = sorted_inputs[0]
        # print(furthest_input)
        # furthest_input.set_position(
        #     sorted_inputs[1].chain_dimension.end_node.position.x - 128 - 96,
        #     furthest_input.position.y
        # )
        # seen = []
        # update_inputs_positions(furthest_input, sorted_inputs[1].chain_dimension.width + SPACER + 96, seen)