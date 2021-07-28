from abc import ABC
from abc import abstractmethod
from dataclasses import dataclass
from typing import Tuple
from typing import List

from common import bw_node
from . import input_alignment_behavior
from . import utils


@dataclass
class PostAlignmentBehavior(ABC):
    """
    Defines the behavior to execute after alignment of each input node is
    finished.
    """
    limit_to_chain: bool = True
    @abstractmethod
    def run(self, node: bw_node.Node):
        pass


class NoPostAlignment(PostAlignmentBehavior):
    def run(self, _):
        pass


class AlignInputsToCenter(PostAlignmentBehavior):
    def run(self, node: bw_node.Node):
        inputs = node.input_nodes(limit_to_chain=self.limit_to_chain)
        if len(inputs) > 1:
            top_input_node = inputs[0]
            bottom_input_node = inputs[-1]

            _, mid_point = utils.calculate_mid_point(top_input_node,
                                                     bottom_input_node)

            for input_node in inputs:
                input_node.offset.y = input_node.pos.y - mid_point
                input_node.refresh_position_using_offset(recursive=True,
                                                         limit_to_chain=self.limit_to_chain)


class AlignNoOverlapAverageCenter(PostAlignmentBehavior):
    def run(self, node: bw_node.Node):
        if len(node.input_nodes(limit_to_chain=True)) < 2:
            return

        top_input_node = node.input_nodes(limit_to_chain=True)[0]
        bottom_input_node = node.input_nodes(limit_to_chain=True)[-1]
        _, mid_point = utils.calculate_mid_point(top_input_node,
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
        for input_node in node.input_nodes(limit_to_chain=True):
            if input_node.pos.y < point:
                nodes_above.append(input_node)
            elif input_node.pos.y > point:
                nodes_below.append(input_node)
        return nodes_above, nodes_below
