import importlib
from dataclasses import dataclass
from dataclasses import field
from typing import List
from typing import Tuple

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
class NodeRootChainAligner():
    on_output_node = 0
    on_finished_output_nodes = 0

    def run(self, node: bw_node.Node, seen: List[bw_node.Node]):
        for i, input_node in enumerate(node.input_nodes()):
            if not input_node.is_root and input_node not in seen:
                self.run(input_node, seen)
                continue

            print(f'Working on {input_node}')
            # seen.append(input_node)

            output_nodes = self._get_output_nodes_with_multiple_outputs(
                input_node
            )
            output_nodes.sort(key=lambda node: node.pos.x, reverse=True)
            if not output_nodes:
                # Align all inputs to center
                return

            for i, output_node in enumerate(output_nodes):
                if i == 0:
                    self._on_first_output_node(input_node, output_node)
                else:
                    # run output node
                    pass
            
            a = pab.AlignInputsToCenter(limit_to_chain=False)
            a.run(output_nodes[0])

            for input_node in output_nodes[0].input_nodes(limit_to_chain=False):
                input_node.update_offset_data(node)
            
            node.refresh_position_using_offset(recursive=True, limit_to_chain=False)




        # node.refresh_positions_using_offset(recursive=True)
        
    
    
    def _on_first_output_node(self, input_node: bw_node.Node, output_node: bw_node.Node):
        node_above, node_below = self._get_immediate_siblings(
            input_node,
            output_node
        )
        if node_above is not None and node_below is not None:
            # in middle
            pass
        elif node_below is not None:    # Input is above
            a = iab.AlignAboveSibling(limit_to_chain=False)
            a.run(input_node, output_node)
        else:   # Input is below
            a = iab.AlignBelowSibling(limit_to_chain=False)
            # a.run(input_node, output_node)
            pass



    def _get_output_nodes_with_multiple_outputs(self,
                                                node: bw_node.Node
                                                ) -> List[bw_node.Node]:
        nodes = list()
        for output_node in node.output_nodes:
            if output_node.input_node_count >= 2:
                nodes.append(output_node)
        return nodes

    def _get_immediate_siblings(self,
                                node: bw_node.Node,
                                output_node: bw_node.Node
                                ) -> Tuple[bw_node.Node, bw_node.Node]:
        for i, input_node in enumerate(output_node.input_nodes()):
            if input_node != node:
                continue
            
            node_above = None
            node_below = None
            if i != 0:
                try:
                    node_above = output_node.input_nodes()[i - 1]
                except IndexError:
                    pass

            try:
                node_below = output_node.input_nodes()[i + 1]
            except IndexError:
                pass

        return node_above, node_below

@dataclass
class InputNodeAligner():
    """
    This class is used to align the inputs of a given node.

    on_first_input: InputNodeAlignmentBehavior = Defines the behavior
    for the first input of a given node.

    on_input_node: InputNodeAlignmentBehavior = Defines the behavior
    for all subsequent nodes after the first.

    on_finished_input_nodes: PostAlignmentBehavior = Is called after
    all inputs have been processed. You can use this behavior to
    apply logic on the newly updated input node positions. For example,
    by aligning them to the center point.
    """
    on_first_input_node: iab.InputNodeAlignmentBehavior = field(init=False)
    on_input_node: iab.InputNodeAlignmentBehavior = field(init=False)
    on_finished_input_nodes: pab.PostAlignmentBehavior = field(init=False)
    limit_to_chain: bool = True

    def run(self, node: bw_node.Node):
        for i, input_node in enumerate(node.input_nodes(self.limit_to_chain)):
            if i == 0:
                self.on_first_input_node.run(input_node, node)
            else:
                self.on_input_node.run(input_node, node)

            if len(input_node.input_nodes(self.limit_to_chain)) > 0:
                self.run(input_node)
        self.on_finished_input_nodes.run(node)

        if node.offset_node is not None:
            node.update_offset_data(node.offset_node)
        for input_node in node.input_nodes():
            input_node.update_offset_data(node)


@dataclass
class HiarachyAlign(InputNodeAligner):
    on_first_input_node = iab.AlignLeftOutput()
    on_input_node = iab.AlignBelowSibling(limit_to_chain=True)
    on_finished_input_nodes = pab.AlignInputsToCenter(limit_to_chain=True)


@dataclass
class RemoveOverlap(InputNodeAligner):
    on_first_input_node = iab.NoInputNodeAlignment()
    on_input_node = iab.NoInputNodeAlignment()
    on_finished_input_nodes = pab.AlignNoOverlapAverageCenter()


@dataclass
class NodeChainAlign(NodeRootChainAligner):
    on_output_node = 0
    on_finished_output_nodes = 0

def run(node_selection: bw_node_selection.NodeSelection):
    # TODO: Add option to reposition roots or not
    # TODO: Add option to align by main line

    for node_chain in node_selection.node_chains:
        if node_chain.root.output_node_count != 0:
            continue
        sort_nodes(node_chain.root)
    
    for node_chain in node_selection.node_chains:
        aligner = HiarachyAlign()
        aligner.run(node_chain.root)
    
    # for node in node_selection.nodes:
    #     print(node.offset_node)
    #     print(node.offset)

    
    # Position all roots starting from the top of tree
    seen = list()
    for node_chain in node_selection.node_chains:
        if node_chain.root.output_node_count != 0:
            continue
        aligner = NodeChainAlign()
        aligner.run(node_chain.root, seen)

        # original_pos = node_chain.root.pos.y
        # aligner = RemoveOverlap()
        # aligner.run(node_chain.root)

        # # move back
        # offset = original_pos - node_chain.root.pos.y
        # node_chain.root.set_position(node_chain.root.pos.x,
        #                              node_chain.root.pos.y + offset)
        # utils.offset_children(node_chain.root, offset)

    for node_chain in node_selection.node_chains:
        pass



def sort_nodes(node: bw_node.Node):
    for input_node in node.input_nodes():
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
