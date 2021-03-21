from typing import List

from common import bw_node
from common import bw_node_selection


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


def run(node_selection: bw_node_selection.NodeSelection):
    build_upstream_data(node_selection)

