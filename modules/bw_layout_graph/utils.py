from common import bw_node


def offset_children(parent_node: bw_node.Node, offset: float):
    for input_node in parent_node.input_nodes_in_same_chain:
        input_node.set_position(input_node.pos.x, input_node.pos.y + offset)
        offset_children(input_node, offset)


def calculate_mid_point(a: bw_node.Node, b: bw_node.Node) -> float:
    x = (a.pos.x + b.pos.x) / 2
    y = (a.pos.y + b.pos.y) / 2

    return x, y


def get_index_in_input_list(input_node: bw_node.Node,
                            output_node: bw_node.Node) -> int:
    for i, node in enumerate(output_node.input_nodes_in_same_chain):
        if node == input_node:
            return i
