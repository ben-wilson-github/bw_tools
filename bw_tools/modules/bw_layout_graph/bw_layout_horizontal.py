from bw_tools.common import bw_node
from bw_tools.common import bw_node_selection

SPACER = 32


def move_node(node: bw_node.Node, queue: list):
    target_node = node.closest_output_node
    if target_node is None:
        target_node = node.output_nodes[0]

    node.set_position(
        target_node.pos.x - SPACER - node.width,
        target_node.pos.y
    )

    if node.has_input_nodes_connected:
        for input_node in node.input_nodes:
            input_node.closest_output_node = node
            queue.append(input_node)


def run(node_selection: bw_node_selection.NodeSelection):
    node_selection.remove_dot_nodes()

    for root_node in node_selection.root_nodes:
        if not root_node.has_input_nodes_connected:
            continue

        queue = []
        for input_node in root_node.input_nodes:
            queue.append(input_node)

        while len(queue) > 0:
            node = queue.pop(0)
            move_node(node, queue)
