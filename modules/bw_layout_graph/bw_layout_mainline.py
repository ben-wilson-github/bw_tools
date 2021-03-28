from typing import List

from common import bw_node
from common import bw_node_selection
from common import bw_chain_dimension

SPACER = 32

def set_branching_property(node: bw_node.Node, running_list: List[bw_node.Node], queue: List[bw_node.Node]):
    if node.is_branching:
        running_list.append(node)

    for input_node in node.input_nodes:
        for cd in input_node.output_connection_data:
            cd.branches = running_list.copy()
        queue.append(input_node)





def build_upstream_data(node_selection: bw_node_selection.NodeSelection):
    queue = []
    running_list = []
    for root_node in node_selection.root_nodes:
        queue.append(root_node)
        while len(queue) > 0:
            node = queue.pop(0)
            set_branching_property(node, running_list=running_list, queue=queue)
            node.add_comment(str(node.output_connection_data))


def update_inputs_positions(node: bw_node.Node, offset, seen):
    for input_node in node.input_nodes:
        if input_node in seen:
            continue
        seen.append(input_node)
        input_node.set_position(input_node.position.x - offset, input_node.position.y)
        if input_node.has_input_nodes_connected:
            update_inputs_positions(input_node, offset, seen)


def run(node_selection: bw_node_selection.NodeSelection):
    # build_upstream_data(node_selection)
    build_downstream_data(node_selection)

    i = 0
    for node in node_selection.input_branching_nodes:
        if i == 1:
            return
        i += 1
        print(node.chain_dimension)
        sorted_inputs = sorted(list(node.input_nodes), key=lambda item: item.chain_dimension.min_x)
        furthest_input = sorted_inputs[0]
        print(furthest_input)
        furthest_input.set_position(
            sorted_inputs[1].chain_dimension.end_node.position.x - 128 - 96,
            furthest_input.position.y
        )
        seen = []
        update_inputs_positions(furthest_input, sorted_inputs[1].chain_dimension.width + SPACER + 96, seen)