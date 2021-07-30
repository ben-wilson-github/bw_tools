from typing import List

from common import bw_node
from . import input_alignment_behavior


SPACER = 32
# During sorting pass
# if processing node is root
#     if processing node is in seen:
#         continue
#     for each output
#         for each input (ecluding the processing node)
#             if this input node has multiple inputs (ie, its going to expand)
#                 then processing node should be static
#                 return
#     if none of the inputs for any of the outputs had mutliple inputs (ie, its not going to expand)
#         then processing node should be dynamic

def sort_nodes2(node: bw_node.Node, already_processed: List[bw_node.Node]):
    for input_node in node.input_nodes:
        do_something(input_node, node, already_processed)
        sort_nodes2(input_node, already_processed)

def calculate_offset(node: bw_node.Node, output_node: bw_node.Node):
    if node.is_root:
        spacer = SPACER * 4
    else:
        spacer = SPACER
    half_output = output_node.width / 2
    half_input = node.width / 2
    return half_output + spacer + half_input


def calculate_behavior(node: bw_node.Node, offset: float):
    if not node.is_root:
        return input_alignment_behavior.StaticAlignment(offset=offset)
    
    CONTINUE TO IMPLEMENT THE CODE ABOVE
    for output_node in node.output_nodes:
        if output_node.input_node_count == 1:
            return input_alignment_behavior.StaticAlignment(offset=offset)

        for input_node in output_node.input_nodes:
            if input_node is node:
                continue

            if input_node.input_node_count > 1:
                # If the input node has multiple inputs connected,
                # then it is likely to expand later.
                # Make it static
                return # the behavior
    return # Dynamic behavior

def do_something(node: bw_node.Node, previous_node: bw_node.Node, already_processed: List[bw_node.Node]):
    # Set an offset node
    if node.offset_node is None or previous_node.pos.x > node.offset_node.pos.x:
        node.offset_node = previous_node

    # Position the node
    offset = calculate_offset(node, node.closest_output_node_in_x)

    if node not in already_processed:
        behavior = calculate_behavior(node, -offset)

    node.set_position(node.closest_output_node_in_x.pos.x - offset,
                      node.closest_output_node_in_x.pos.y)




    

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
        input_node.offset = bw_node.Float2(
            -desired_offset, 0
        )

        pos = output_node.pos.x - desired_offset

        input_node.set_position(pos, input_node.pos.y)
        sort_nodes(input_node)
