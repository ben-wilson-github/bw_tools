from abc import ABC
from abc import abstractmethod
from typing import Tuple
from typing import List

from common import bw_node
from . import input_alignment_behavior
from . import utils


class PostAlignmentBehavior(ABC):
    """
    Defines the behavior to execute after alignment of each input node is
    finished.
    """
    @abstractmethod
    def run(self, node: bw_node.Node):
        pass


class NoPostAlignment(PostAlignmentBehavior):
    def run(self, _):
        pass


class AlignInputsToBottom(PostAlignmentBehavior):
    def run(self, node: bw_node.Node):
        if len(node.input_nodes_in_same_chain) > 1:
            bottom_input_node = node.input_nodes_in_same_chain[-1]

            offset = bottom_input_node.pos.y - node.pos.y
            bw_layout_utils.offset_children(node, offset=-offset)


class AlignInputsToCenter(PostAlignmentBehavior):
    def run(self, node: bw_node.Node):
        if len(node.input_nodes_in_same_chain) > 1:
            top_input_node = node.input_nodes_in_same_chain[0]
            bottom_input_node = node.input_nodes_in_same_chain[-1]

            _, y = bw_layout_utils.calculate_mid_point(top_input_node,
                                                       bottom_input_node)
            offset = y - node.pos.y
            bw_layout_utils.offset_children(node, offset=-offset)


class AlignNoOverlapAverageCenter(PostAlignmentBehavior):
    def run(self, node: bw_node.Node):
        if len(node.input_nodes_in_same_chain) < 2:
            return

        top_input_node = node.input_nodes_in_same_chain[0]
        bottom_input_node = node.input_nodes_in_same_chain[-1]
        _, mid_point = bw_layout_utils.calculate_mid_point(top_input_node,
                                                           bottom_input_node)

        nodes_above, nodes_below = self._get_input_nodes_around_point(
            node,
            mid_point
        )
        nodes_above.reverse()

        for input_node in nodes_above:
            align = input_alignment_behavior.AlignChainAboveSibling()
            align.run(input_node, node)

        for input_node in nodes_below:
            align = input_alignment_behavior.AlignChainBelowSibling()
            align.run(input_node, node)

        align = AlignInputsToCenter()
        align.run(node)

    def _get_input_nodes_around_point(
            self,
            node: bw_node.Node,
            point: float
            ) -> Tuple[List[bw_node.Node], List[bw_node.Node]]:
        nodes_above = list()
        nodes_below = list()
        for input_node in node.input_nodes_in_same_chain:
            if input_node.pos.y < point:
                nodes_above.append(input_node)
            elif input_node.pos.y > point:
                nodes_below.append(input_node)
        return nodes_above, nodes_below
