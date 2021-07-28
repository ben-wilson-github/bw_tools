from abc import ABC
from abc import abstractmethod
from dataclasses import dataclass

from typing import Tuple

from common import bw_node
from common import bw_node_selection
from common import bw_chain_dimension

from . import utils


SPACER = 32


@dataclass
class InputNodeAlignmentBehavior(ABC):
    """
    Defines the behavior for positioning a single input node relative
    to a connected output noode.

    You must reimplement the run method with the logic for positioning
    the node.

    You must pass in the input node, the connected output node and the
    index in which the input node connects into the output node
    """
    limit_to_chain: bool = True

    @abstractmethod
    def run(self, input_node: bw_node.Node, output_node: bw_node.Node):
        pass

    @abstractmethod
    def get_sibling_node(self,
                         input_node: bw_node.Node,
                         output_node: bw_node.Node) -> bw_node.Node:
        pass


class NoInputNodeAlignment(InputNodeAlignmentBehavior):
    def run(self, input_node: bw_node.Node, output_node: bw_node.Node):
        pass

    def get_sibling_node(self, _, __) -> bw_node.Node:
        pass


class AlignWithOutput(InputNodeAlignmentBehavior):
    def run(self, input_node: bw_node.Node, output_node: bw_node.Node):
        input_node.set_position(input_node.pos.x, output_node.pos.y)

    def get_sibling_node(self, _, __) -> bw_node.Node:
        pass


class AlignBelowSibling(InputNodeAlignmentBehavior):
    def run(self, input_node: bw_node.Node, output_node: bw_node.Node):
        node_above = self.get_sibling_node(input_node, output_node)
        try:
            cd = bw_chain_dimension.calculate_chain_dimension(
                node_above,
                output_node.chain,
                limit_bounds=bw_chain_dimension.Bound(
                    left=input_node.pos.x
                )
            )
        except bw_chain_dimension.OutOfBoundsError:
            # The node above might be outside of the bounds
            # so this will fail. This can happen if the
            # input node outputs to the same parent more than
            # once
            pass
        else:
            new_pos_y = cd.bounds.lower + SPACER + input_node.height / 2
            input_node.set_position(input_node.pos.x, new_pos_y)

    def get_sibling_node(self,
                         input_node: bw_node.Node,
                         output_node: bw_node.Node) -> bw_node.Node:
        i = output_node.input_nodes.index(input_node)
        return output_node.input_nodes[i - 1]


class AlignBelowSiblingInSameChain(AlignBelowSibling):
    def get_sibling_node(self,
                         input_node: bw_node.Node,
                         output_node: bw_node.Node) -> bw_node.Node:
        i = output_node.input_nodes_in_chain.index(input_node)
        return output_node.input_nodes_in_chain[i - 1]


class AlignAboveSibling(InputNodeAlignmentBehavior):
    def run(self, input_node: bw_node.Node, output_node: bw_node.Node):
        node_below = self.get_sibling_node(input_node, output_node)
        try:
            cd = bw_chain_dimension.calculate_chain_dimension(
                node_below,
                output_node.chain,
                limit_bounds=bw_chain_dimension.Bound(
                    left=input_node.pos.x
                )
            )
        except bw_chain_dimension.OutOfBoundsError:
            pass
        else:
            new_pos_y = cd.bounds.upper - SPACER - input_node.height / 2
            input_node.set_position(input_node.pos.x, new_pos_y)

    def get_sibling_node(self,
                         input_node: bw_node.Node,
                         output_node: bw_node.Node) -> bw_node.Node:
        i = output_node.input_nodes.index(input_node)
        return output_node.input_nodes[i + 1]


class AlignAboveSiblingInSameChain(AlignAboveSibling):
    def get_sibling_node(self,
                         input_node: bw_node.Node,
                         output_node: bw_node.Node) -> bw_node.Node:
        i = output_node.input_nodes_in_chain.index(input_node)
        return output_node.input_nodes_in_chain[i + 1]

# ===========================================================
# Chain Align Behavior
# ===========================================================


class AlignSmallestChainBehavior(InputNodeAlignmentBehavior, ABC):
    @abstractmethod
    def calculate_offset(self,
                         input_node: bw_node.Node,
                         sibling_node: bw_node.Node,
                         smallest_cd: bw_chain_dimension.ChainDimension,
                         chain: bw_node_selection.NodeChain
                         ) -> float:
        pass

    def run(self,
            input_node: bw_node.Node,
            output_node: bw_node.Node):

        sibling_node = self.get_sibling_node(input_node, output_node)

        smallest_cd = self._calculate_smallest_chain_dimension(
            input_node,
            sibling_node,
            output_node.chain
        )

        offset = self.calculate_offset(input_node,
                                       sibling_node,
                                       smallest_cd,
                                       output_node.chain)

        input_node.set_position(input_node.pos.x, input_node.pos.y + offset)

    @staticmethod
    def _calculate_smallest_chain_dimension(
        a: bw_node.Node,
        b: bw_node.Node,
        chain: bw_node_selection.NodeChain
    ) -> bw_chain_dimension.ChainDimension:
        a_cd = bw_chain_dimension.calculate_chain_dimension(a, chain=chain)
        b_cd = bw_chain_dimension.calculate_chain_dimension(b, chain=chain)
        smallest = a_cd

        if a_cd.bounds.left > b_cd.bounds.left:
            smallest = a_cd
        elif a_cd.bounds.left == b_cd.bounds.left:
            if a_cd.bounds.upper >= b_cd.bounds.upper:
                smallest = a_cd
            else:
                smallest = b_cd
        else:
            smallest = b_cd
        return smallest

    @staticmethod
    def _get_upper_bound_info(node: bw_node.Node,
                              chain: bw_node_selection.NodeChain,
                              left_bound_limit: float
                              ) -> Tuple[float, float]:
        try:
            cd = bw_chain_dimension.calculate_chain_dimension(
                node,
                chain,
                limit_bounds=bw_chain_dimension.Bound(
                    left=left_bound_limit
                )
            )
        except bw_chain_dimension.OutOfBoundsError:
            bound_x = node.pos.x
            bound_y = node.pos.y - node.height / 2
        else:
            bound_x = cd.upper_node.pos.x
            bound_y = cd.bounds.upper

        return bound_x, bound_y

    @staticmethod
    def _get_lower_bound_info(node: bw_node.Node,
                              chain: bw_node_selection.NodeChain,
                              left_bound_limit: float
                              ) -> Tuple[float, float]:
        try:
            cd = bw_chain_dimension.calculate_chain_dimension(
                node,
                chain,
                limit_bounds=bw_chain_dimension.Bound(
                    left=left_bound_limit
                )
            )
        except bw_chain_dimension.OutOfBoundsError:
            bound_x = node.pos.x
            bound_y = node.pos.y + node.height / 2
        else:
            bound_x = cd.lower_node.pos.x
            bound_y = cd.bounds.lower

        return bound_x, bound_y


class AlignBelowSiblingSmallestChain(AlignSmallestChainBehavior):
    def calculate_offset(self,
                         input_node: bw_node.Node,
                         sibling_node: bw_node.Node,
                         smallest_cd: bw_chain_dimension.ChainDimension,
                         chain: bw_node_selection.NodeChain
                         ) -> float:
        input_bound_x, input_bound_y = self._get_upper_bound_info(
            input_node,
            chain,
            smallest_cd.bounds.left
        )
        _, sibling_bound_y = self._get_lower_bound_info(
            sibling_node,
            chain,
            input_bound_x
        )
        return (sibling_bound_y + SPACER) - input_bound_y

    def get_sibling_node(self,
                         input_node: bw_node.Node,
                         output_node: bw_node.Node) -> bw_node.Node:
        i = output_node.input_nodes.index(input_node)
        return output_node.input_nodes[i - 1]


class AlignAboveSiblingSmallestChain(AlignSmallestChainBehavior):
    def calculate_offset(self,
                         input_node: bw_node.Node,
                         sibling_node: bw_node.Node,
                         smallest_cd: bw_chain_dimension.ChainDimension,
                         chain: bw_node_selection.NodeChain
                         ) -> float:
        sibling_bound_x, sibling_bound_y = self._get_upper_bound_info(
            sibling_node,
            chain,
            smallest_cd.bounds.left
        )
        _, input_bound_y = self._get_lower_bound_info(
            input_node,
            chain,
            sibling_bound_x
        )
        return (sibling_bound_y - SPACER) - input_bound_y

    def get_sibling_node(self,
                         input_node: bw_node.Node,
                         output_node: bw_node.Node) -> bw_node.Node:
        i = output_node.input_nodes.index(input_node)
        return output_node.input_nodes[i + 1]
