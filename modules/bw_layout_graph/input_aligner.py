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
    on_first: iab.InputNodeAlignmentBehavior = field(init=False)
    on_input: iab.InputNodeAlignmentBehavior = field(init=False)
    on_finished: pab.PostAlignmentBehavior = field(init=False)

    def run(self, node: bw_node.Node):
        for i, input_node in enumerate(node.input_nodes_in_chain):
            if i == 0:
                self.on_first.run(input_node, node)
            else:
                self.on_input.run(input_node, node)

            if input_node.input_nodes_in_chain_count > 0:
                self.run(input_node)

        self.on_finished.run(node)

        if node.offset_node is not None:
            node.update_offset_to_node(node.offset_node)
        input_node: bw_node.Node
        for input_node in node.input_nodes:
            input_node.update_offset_to_node(node)


@dataclass
class HiarachyAlign(InputNodeAligner):
    on_first = iab.AlignWithOutput()
    on_input = iab.AlignBelowSibling()
    on_finished = pab.AlignChainInputsToCenterPoint()


@dataclass
class RemoveOverlap(InputNodeAligner):
    on_first = iab.NoInputNodeAlignment()
    on_input = iab.NoInputNodeAlignment()
    on_finished = pab.AlignNoOverlapAverageCenter()
