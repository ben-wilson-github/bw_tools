import importlib
from dataclasses import dataclass
from dataclasses import field

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

    def run(self, node: bw_node.Node):
        for i, input_node in enumerate(node.input_nodes_in_same_chain):
            if i == 0:
                self.on_first_input_node.run(input_node, node)
            else:
                self.on_input_node.run(input_node, node)

            if len(input_node.input_nodes_in_same_chain) > 0:
                self.run(input_node)
        self.on_finished_input_nodes.run(node)


@dataclass
class HiarachyAlign(InputNodeAligner):
    on_first_input_node = iab.AlignLeftOutput()
    on_input_node = iab.AlignBelowSibling()
    on_finished_input_nodes = pab.AlignInputsToCenter()


@dataclass
class RemoveOverlap(InputNodeAligner):
    on_first_input_node = iab.NoInputNodeAlignment()
    on_input_node = iab.NoInputNodeAlignment()
    on_finished_input_nodes = pab.AlignNoOverlapAverageCenter()


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

        original_pos = node_chain.root.pos.y
        aligner = RemoveOverlap()
        aligner.run(node_chain.root)

        # move back
        offset = original_pos - node_chain.root.pos.y
        node_chain.root.set_position(node_chain.root.pos.x,
                                     node_chain.root.pos.y + offset)
        utils.offset_children(node_chain.root, offset)

        # aligner = InputNodeAligner(
        #     on_first_input_node=NoInputNodeAlignment(),
        #     on_input_node=AlignChainBelowSibling(),
        #     on_finished_input_nodes=NoPostAlignment()
        # )
        # aligner.run(node_chain.root)
        # MNaybe apåply offset instead of centering

        # layout_y_axis(node_chain.root)
        # IMPLEMENT LOGIC I WROTE IN TEST FILE
        # OVERLAP IS NOT WORKING AGAIN
        # remove_overlap_in_children(node_chain.root)

        # queue.clear()
        # populate_queue(node_chain.root, queue)
        # while queue:
        #     node = queue.pop(0)
        #     layout_y_axis(node, queue)

    # remove_overlap_in_children(root_node)


def sort_nodes(node: bw_node.Node):
    for input_node in node.input_nodes:
        output_node = input_node.closest_output_node_in_x
        half_output = output_node.width / 2
        half_input = input_node.width / 2

        if input_node.is_root:
            spacer = SPACER * 4
        else:
            spacer = SPACER

        pos = output_node.pos.x - half_output - spacer - half_input

        input_node.set_position(pos, input_node.pos.y)
        sort_nodes(input_node)
