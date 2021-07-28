from common import bw_node

SPACER = 32


def sort_nodes(node: bw_node.Node):
    input_node: bw_node.Node
    for input_node in node.input_nodes:
        output_node = input_node.closest_output_node_in_x
        input_node.offset_node = output_node

        half_output = output_node.width / 2
        half_input = input_node.width / 2

        if input_node.is_root:
            spacer = SPACER * 4
        else:
            spacer = SPACER

        desired_offset = half_output + spacer + half_input
        input_node.offset = bw_node.NodePosition(
            -desired_offset, 0
        )

        pos = output_node.pos.x - desired_offset

        input_node.set_position(pos, input_node.pos.y)
        sort_nodes(input_node)
