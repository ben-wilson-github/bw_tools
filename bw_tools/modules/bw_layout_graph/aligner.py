import importlib
from dataclasses import dataclass
from dataclasses import field
from typing import List

from bw_tools.common.bw_node import Node, Float2
from bw_tools.common import bw_node_selection
from bw_tools.common import bw_chain_dimension

from . import utils
from . import post_alignment_behavior as pab
from . import alignment_behavior

importlib.reload(pab)
importlib.reload(alignment_behavior)
importlib.reload(utils)
importlib.reload(bw_node_selection)
importlib.reload(bw_chain_dimension)


SPACER = 32


@dataclass
class HiarachyAlign():
    def run(self, node: Node):
        for i, input_node in enumerate(node.input_nodes_in_chain):
            if i == 0:
                iab.align_in_line(input_node, node)
            else:
                i = node.input_nodes_in_chain.index(input_node)
                sibling_node = node.input_nodes_in_chain[i - 1]
                iab.align_below(input_node, sibling_node)

        if node.input_nodes_in_chain_count >= 2:
            pab.average_positions_relative_to_node(node.input_nodes_in_chain, node)

        input_node: Node
        for input_node in node.input_nodes_in_chain:
            input_node.update_offset_to_node(node)

        for input_node in node.input_nodes_in_chain:
            if input_node.input_nodes_in_chain_count > 0:
                self.run(input_node)


@dataclass
class RemoveOverlap():
    def run(self, node: Node):
        for input_node in node.input_nodes_in_chain:
            if input_node.input_nodes_in_chain_count > 0:
                self.run(input_node)

        pab.remove_overlap(node, node.input_nodes_in_chain)

    def run2(self, node: Node, seen: List[Node]):
        print(node)
        if not node.has_input_nodes_connected:
            print('returning')
            return

        for input_node in node.input_nodes:
            self.run2(input_node, seen)

        if node.input_node_count >= 2 and node not in seen:
            pab.remove_overlap2(node, node.input_nodes, seen)

def run_remove_overlap(node: Node, already_processed: List[Node]):
    if not node.has_input_nodes_connected:
        return
    
    for input_node in node.input_nodes:
        run_remove_overlap(input_node)
    
    if node.has_branching_inputs and node not in already_processed:
        already_processed.append(node)
        process_node_remove_overlap(node, already_processed)

def process_node_remove_overlap(node, already_processed):
    pass

    

def run_aligner(node: Node, already_processed: List[Node], roots_to_update: List[Node], node_selection):
    if not node.has_input_nodes_connected:
        return

    inputs = list(node.input_nodes)
    inputs.reverse()
    # inputs.reverse()
    for input_node in inputs:
        run_aligner(input_node, already_processed, roots_to_update, node_selection)

    if node.has_branching_inputs and node not in already_processed:
        already_processed.append(node)
        process_node(node, already_processed, roots_to_update, node_selection)


def process_node(node: Node, already_processed: List[Node], roots_to_update: List[Node], node_selection):
    stack_inputs(node, roots_to_update, node_selection)
    if node.identifier == 1:
        raise AttributeError()
    # resolve_alignment_stack(node, roots_to_update)
    resolve_alignment_average(node)
    for root_node in roots_to_update:
        root_node.alignment_behavior.exec()
        root_node.update_chain_positions()
    
    for input_node in node.input_nodes:
        root_nodes = input_node.find_root_nodes_in_chain()
        for root in root_nodes:
            if root not in roots_to_update:
                roots_to_update.append(root)

    if node.identifier == 1:
        raise AttributeError()

def resolve_alignment_average(node: Node):
    _, mid_point = utils.calculate_mid_point(node.input_nodes[0],
                                             node.input_nodes[-1])
    offset = node.pos.y - mid_point

    for input_node in node.input_nodes:
        # if node is not input_node.alignment_behavior.offset_node:
        #     input_node.alignment_behavior.exec()

        new_pos = Float2(input_node.pos.x, input_node.pos.y + offset)
        input_node.alignment_behavior.update_offset(new_pos)
        input_node.alignment_behavior.exec()
        input_node.update_all_chain_positions()
    return

def resolve_alignment_stack(node: Node, roots_to_update) -> List[Node]:
    for input_node in node.input_nodes:
        # if node is not input_node.alignment_behavior.offset_node:
        #     input_node.alignment_behavior.exec() 
        # else:
        new_pos = Float2(input_node.pos.x, input_node.pos.y)
        input_node.alignment_behavior.update_offset(new_pos)
        input_node.update_chain_positions()
    return

def stack_inputs(node: Node, already_process: List[Node], node_selection):
    for i, input_node in enumerate(node.input_nodes):
        if i == 0:
            print(f'First input -> Moving inline with {node}')
            alignment_behavior.align_in_line(input_node, node)
            input_node.alignment_behavior.offset_node = node
            new_pos = Float2(input_node.pos.x, input_node.pos.y)
            input_node.alignment_behavior.update_offset(new_pos)
            # input_node.update_chain_positions()
            input_node.update_all_chain_positions()
            if node.identifier == 1:
                raise AttributeError()
        else:
            print(f'Next input -> Attempting to align below')
            alignment_behavior.align_below_shortest_chain_dimension(input_node, node, i, node_selection)
            if node.identifier == 1:
                raise AttributeError()
            # input_node.update_chain_positions()
            input_node.alignment_behavior.offset_node = node
            new_pos = Float2(input_node.pos.x, input_node.pos.y)
            input_node.alignment_behavior.update_offset(new_pos)
            input_node.update_all_chain_positions()
    return