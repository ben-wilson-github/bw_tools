from common import bw_node
from common import bw_node_selection

SPACER = 32


def get_height_sum_from_largest_chain_to_node(node: bw_node.Node, target_node: bw_node.Node):
    index_to_move = node.indices_in_target(target_node)[0]
    largest_chain_index = target_node.largest_chain_depth_index

    if index_to_move > largest_chain_index:
        increment = 1
        start = largest_chain_index + 1
    else:
        increment = -1
        start = largest_chain_index - 1

    value = 0
    for i in range(start, index_to_move, increment):
        height = target_node.input_node_height_in_index(i)
        if height > 0:
            value += height + SPACER

    return value


def get_y_offset_from_target(node: bw_node.Node, target_node: bw_node.Node) -> float:
    sum = get_height_sum_from_largest_chain_to_node(node, target_node)
    offset = sum + (node.height / 2) + (SPACER / 2)
    return offset


def move_node_below_target(node: bw_node.Node, target_node: bw_node.Node):
    node.set_position(
        target_node.position.x - SPACER - node.width,
        target_node.position.y + get_y_offset_from_target(node, target_node)
    )


def move_node_above_target(node: bw_node.Node, target_node: bw_node.Node):
    node.set_position(
        target_node.position.x - SPACER - node.width,
        target_node.position.y - get_y_offset_from_target(node, target_node)
    )


def move_node_inline_with_target(node: bw_node.Node, target_node: bw_node.Node):
    node.set_position(
        target_node.position.x - SPACER - node.width,
        target_node.position.y
    )


def sum_of_all_input_nodes_above(target_index: int, target_node: bw_node.Node) -> float:
    value = 0
    for i in range(target_index + 1):
        input_node_height = target_node.input_node_height_in_index(i)
        value += input_node_height
        if input_node_height > 0:
            value += SPACER
    return value


def move_node_even_distance(node: bw_node.Node, target_node: bw_node.Node):
    target_delta_from_norm = (target_node.height - 96) / 2
    current_delta_from_norm = (node.height - 96) / 2
    y_offset = target_delta_from_norm - current_delta_from_norm

    target_index = node.indices_in_target(target_node)[0]
    y_offset += sum_of_all_input_nodes_above(target_index, target_node)
    y_offset -= SPACER  # Remove the first spacer
    additional_spacing = (target_node.input_node_count - 1) * SPACER

    node.set_position(
        target_node.position.x - SPACER - node.width,
        target_node.position.y + y_offset - (target_node.height / 2)
        - ((target_node.input_nodes_height_sum + additional_spacing) / 2)
    )


def move_node(node: bw_node.Node, queue: list):
    target_node = node.closest_output_node
    if target_node is None:
        target_node = node.output_nodes[0]

    print(f'moving {node.label} to {target_node.label}')

    if target_node.input_node_count == 1:
        move_node_inline_with_target(node, target_node)
    elif target_node.input_chains_are_equal_depth:
        move_node_even_distance(node, target_node)
    else:
        if node.is_largest_chain_in_target(target_node):
            move_node_inline_with_target(node, target_node)
        elif node.connects_above_largest_chain_in_target(target_node):
            move_node_above_target(node, target_node)
        elif node.connects_below_largest_chain_in_target(target_node):
            move_node_below_target(node, target_node)

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
