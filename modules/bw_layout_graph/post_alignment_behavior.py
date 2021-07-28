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
    @abstractmethod
    def run(self, node: bw_node.Node):
        pass


class NoPostAlignment(PostAlignmentBehavior):
    def run(self, _):
        pass


@dataclass
class AlignInputsToCenterPoint(PostAlignmentBehavior):
    def run(self, node: bw_node.Node):
        inputs = node.input_nodes_in_chain

        if len(inputs) < 2:
            return

        top_input_node = inputs[0]
        bottom_input_node = inputs[-1]

        _, mid_point = utils.calculate_mid_point(top_input_node,
                                                 bottom_input_node)

        offset = node.pos.y - mid_point

        for input_node in inputs:
            input_node.set_position(input_node.pos.x,
                                    input_node.pos.y + offset)
            self.on_after_position_node(input_node)

    @abstractmethod
    def on_after_position_node(self, input_node: bw_node.Node):
        pass


class AlignInputsToCenterPointUpdateChain(AlignInputsToCenterPoint):
    def on_after_position_node(self, input_node: bw_node.Node):
        input_node.update_offset_to_node(input_node.offset_node)
        input_node.refresh_positions()


class AlignInputsToCenterPointOneNode(AlignInputsToCenterPoint):
    def on_after_position_node(self, input_node: bw_node.Node):
        pass


class AlignNoOverlapAverageCenter(PostAlignmentBehavior):
    def run(self, node: bw_node.Node):
        if node.input_nodes_in_chain_count < 2:
            return

        top_input_node = node.input_nodes_in_chain[0]
        bottom_input_node = node.input_nodes_in_chain[-1]
        _, mid_point = utils.calculate_mid_point(top_input_node,
                                                 bottom_input_node)

        nodes_above, nodes_below = self._get_input_nodes_around_point(
            node,
            mid_point
        )

        nodes_above.reverse()

        for input_node in nodes_above:
            align = input_alignment_behavior.AlignAboveSiblingSmallestChain()
            align.run(input_node, node)
            input_node.update_offset_to_node(input_node.offset_node)
            input_node.refresh_positions()

        for input_node in nodes_below:
            align = input_alignment_behavior.AlignBelowSiblingSmallestChain()
            align.run(input_node, node)
            input_node.update_offset_to_node(input_node.offset_node)
            input_node.refresh_positions()

        align = AlignInputsToCenterPointUpdateChain()
        align.run(node)

    def _get_input_nodes_around_point(
            self,
            node: bw_node.Node,
            point: float
            ) -> Tuple[List[bw_node.Node], List[bw_node.Node]]:
        nodes_above = list()
        nodes_below = list()
        for input_node in node.input_nodes_in_chain:
            if input_node.pos.y < point:
                nodes_above.append(input_node)
            elif input_node.pos.y > point:
                nodes_below.append(input_node)
        return nodes_above, nodes_below
