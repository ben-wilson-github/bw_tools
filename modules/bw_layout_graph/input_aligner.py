import importlib
from dataclasses import dataclass
from dataclasses import field
from typing import List

from common import bw_node
from common import bw_node_selection
from common import bw_chain_dimension

from . import utils
from . import post_alignment_behavior as pab
from . import input_alignment_behavior as iab

importlib.reload(pab)
importlib.reload(iab)
importlib.reload(utils)
importlib.reload(bw_node)
importlib.reload(bw_node_selection)
importlib.reload(bw_chain_dimension)


SPACER = 32


@dataclass
class HiarachyAlign():
    def run(self, node: bw_node.Node):
        for i, input_node in enumerate(node.input_nodes_in_chain):
            if i == 0:
                iab.align_in_line(input_node, node)
            else:
                i = node.input_nodes_in_chain.index(input_node)
                sibling_node = node.input_nodes_in_chain[i - 1]
                iab.align_below(input_node, sibling_node)

        if node.input_nodes_in_chain_count >= 2:
            pab.average_positions_relative_to_node(node.input_nodes_in_chain, node)

        input_node: bw_node.Node
        for input_node in node.input_nodes_in_chain:
            input_node.update_offset_to_node(node)

        for input_node in node.input_nodes_in_chain:
            if input_node.input_nodes_in_chain_count > 0:
                self.run(input_node)




    
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
            

@dataclass
class RemoveOverlap():
    def run(self, node: bw_node.Node):
        for input_node in node.input_nodes_in_chain:
            if input_node.input_nodes_in_chain_count > 0:
                self.run(input_node)

        pab.remove_overlap(node, node.input_nodes_in_chain)

    def run2(self, node: bw_node.Node, seen: List[bw_node.Node]):
        print(node)
        if not node.has_input_nodes_connected:
            print('returning')
            return

        for input_node in node.input_nodes:
            self.run2(input_node, seen)

        if node.input_node_count >= 2 and node not in seen:
            pab.remove_overlap2(node, node.input_nodes, seen)
