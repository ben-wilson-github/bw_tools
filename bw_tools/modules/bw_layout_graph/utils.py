from typing import Tuple

from bw_tools.common.bw_node import Node


def calculate_mid_point(a: Node, b: Node) -> Tuple[float, float]:
    x = (a.pos.x + b.pos.x) / 2
    y = (a.pos.y + b.pos.y) / 2

    return x, y


def get_index_in_input_list(
    input_node: Node, output_node: Node, limit_chain: bool = True
) -> int:
    for i, node in enumerate(output_node.input_nodes(limit_chain)):
        if node == input_node:
            return i
