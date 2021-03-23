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


def calculate_chain_dimension(node: bw_node.Node):

    chain_dimension = bw_chain_dimension.ChainDimension(
        max_x=node.position.x + (node.width / 2),
        min_x=node.position.x - (node.width / 2),
        max_y=node.position.y + (node.height / 2),
        min_y=node.position.y - (node.height / 2)
    )
    node.chain_dimension = chain_dimension

    # for output_node in node.output_nodes:
    #     output_node_max_x = output_node.position.x - (output_node.width / 2) - SPACER
    #     chain_dimension.max_x = max(chain_dimension.max_x, output_node_max_x)

    for input_node in node.input_nodes:
        if not input_node.has_branching_outputs and input_node.chain_dimension is not None:
            chain_dimension.min_x = min(input_node.chain_dimension.min_x, chain_dimension.min_x)
            chain_dimension.min_y = min(input_node.chain_dimension.min_y, chain_dimension.min_y)
            chain_dimension.max_y = max(input_node.chain_dimension.max_y, chain_dimension.max_y)

    for output_node in node.output_nodes:
        calculate_chain_dimension(output_node)


def build_downstream_data(node_selection: bw_node_selection.NodeSelection):
    for node in node_selection.end_nodes:
        calculate_chain_dimension(node)

        in order to move the node back, we must track the last node in the chain


def build_upstream_data(node_selection: bw_node_selection.NodeSelection):
    queue = []
    running_list = []
    for root_node in node_selection.root_nodes:
        queue.append(root_node)
        while len(queue) > 0:
            node = queue.pop(0)
            set_branching_property(node, running_list=running_list, queue=queue)
            node.add_comment(str(node.output_connection_data))


def run(node_selection: bw_node_selection.NodeSelection):
    # build_upstream_data(node_selection)
    build_downstream_data(node_selection)

    for node in node_selection.input_branching_nodes:
        sorted_inputs = sorted(list(node.input_nodes), key=lambda item: item.chain_dimension.min_x)
        furthest_input = sorted_inputs[0]
        furthest_input.set_position(
            sorted_inputs[1].position.x - 128,
            furthest_input.position.y
        )
