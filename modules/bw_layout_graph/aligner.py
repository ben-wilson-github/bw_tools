import importlib
from dataclasses import dataclass
from dataclasses import field
from typing import List

from common.bw_node import Node, Float2
from common import bw_node_selection
from common import bw_chain_dimension

from . import utils
from . import post_alignment_behavior as pab
from . import alignment_behavior as ab

importlib.reload(pab)
importlib.reload(ab)
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


    
# go to bottom of the chain
# if node is branching input node
#     for each input in all the input nodes (Stacking the inputs)
#         if it is the first time
#             move inline with the branching node
#             refresh the chain (not the root)
#             add to averaging list
#         else
#             if it is a root
#                 and at least one of its outputs is normal (not branching)
#                     and it only has 1 farest output
#                         and processing node is not the that farest output
#                             add to excluded list
#             else
#                 move node below the chain above, using smallest cd
#                 refresh the chain (not the root)
#                 add to averaging list

#     if averaging list is 2 or more
#         calculate the mid point
#             for each input in the averaging list
#                 try to add offset to align behavior
#                     mvoe it to get new pos
#                     add offset to align behavior

#                 move it by align behavior (if its static it will offset, if not it will average)
#                 refresh the chain (not including the root)
#                 if new pos is not old pos
#                     add it to a moved list
                    
#         then update any previously seen roots
#             for each seen root
#                 move by align behavior
#                 refresh the chain (including the root)
    
#     then add any roots to seen root list
#         for each input
#             if its a root and in the moved list
#                 then add it to seen root list


def begin(node: Node, seen: List[Node]):
    if not node.has_input_nodes_connected:
        return

    for input_node in node.input_nodes:
        begin(input_node, seen)

    if node.input_node_count >= 2 and node not in seen:
        nodes_to_stack, nodes_to_skip = stack_inputs(node)
        align_back(node, nodes_to_stack, nodes_to_skip)

def align_back(node: Node, nodes_to_stack, nodes_to_skip):
    print(f'Aligning back')
    _, mid_point = utils.calculate_mid_point(node.input_nodes[0],
                                             node.input_nodes[-1])
    offset = node.pos.y - mid_point
    
    print(f'Nodes to stack : {nodes_to_stack}')
    print(f'Nodes to skip : {nodes_to_skip}')
    moved = list()
    input_node: Node
    for input_node in nodes_to_stack:
        # try
        print(f'Trying to update offset using {input_node.alignment_behavior}')
        try:
            new_pos = Float2(input_node.pos.x, input_node.pos.y + offset)
            input_node.alignment_behavior.update_offset(new_pos)
            print(f'After updating {input_node.alignment_behavior}')
        except AttributeError:  # Dynamic behaviors do not have an update_offset function
            pass
        
        print(f'Moving {input_node}')
        old_pos = Float2(input_node.pos.x, input_node.pos.y)
        input_node.alignment_behavior.exec()
        input_node.update_chain_positions()

        if input_node.pos != old_pos:
            moved.append(input_node)
    
    if node.identifier == 1419655428:
        raise AttributeError()
    
    # then update any previously seen roots
    # for each seen root
    #     move by align behavior
    #     refresh the chain (including the root)



def stack_inputs(node: Node):
    print(f'Stacking inputs for {node}')

    include: List[Node] = list()
    exclude: List[Node] = list()
    for i, input_node in enumerate(node.input_nodes):
        if i == 0:
            print(f'First input -> Moving inline with {node}')
            ab.align_in_line(input_node, node)
            input_node.update_chain_positions()
            include.append(input_node)
        else:
            print(f'Next input -> Attempting to align below')
            if (input_node.is_root
                    # Any output is not of type branching input
                    and any(output_node.input_node_count < 2 for output_node in input_node.input_nodes)
                    # There is a problem with this logic, its not valid
                    and len(input_node.farthest_output_nodes) == 1
                    and input_node.farthest_output_nodes[0] is not node):
                exclude.append(input_node)
                print(f'Added to exclude instead : {input_node}')
            else:
                print(f'Doing align...')
                ab.align_below_shortest_chain_dimension(input_node, node, i)
                input_node.update_chain_positions()
                include.append(input_node)
    
    return include, exclude

# for each input in all the input nodes (Stacking the inputs)
#         if it is the first time
#             move inline with the branching node
#             refresh the chain (not the root)
#             add to averaging list
#         else
#             if it is a root
#                 and at least one of its outputs is normal (not branching)
#                     and it only has 1 farest output
#                         and processing node is not the that farest output
#                             add to excluded list
#             else
#                 move node below the chain above, using smallest cd
#                 refresh the chain (not the root)
#                 add to averaging list
