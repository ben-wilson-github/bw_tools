from dataclasses import dataclass
import importlib
from abc import ABC
from abc import abstractmethod

from typing import Tuple
from typing import List
from typing import Union

from common import bw_node
from common import bw_node_selection
from common import bw_chain_dimension

importlib.reload(bw_chain_dimension)


SPACER = 32


class PostAlignmentBehavior(ABC):
    """
    Defines the behavior to execute after alignment of each input node is finished.
    """
    @abstractmethod
    def run(self, node: bw_node.Node):
        pass


class NoPostAlignment(PostAlignmentBehavior):
    def run(self, node: bw_node.Node):
        pass


class AlignInputsToBottom(PostAlignmentBehavior):
    def run(self, node: bw_node.Node):
        if len(node.input_nodes_in_same_chain) > 1:
            bottom_input_node = node.input_nodes_in_same_chain[-1]

            offset = bottom_input_node.pos.y - node.pos.y
            offset_children(node, offset=-offset)


class AlignInputsToCenter(PostAlignmentBehavior):
    def run(self, node: bw_node.Node):
        if len(node.input_nodes_in_same_chain) > 1:
            top_input_node = node.input_nodes_in_same_chain[0]
            bottom_input_node = node.input_nodes_in_same_chain[-1]

            _, y = calculate_mid_point(top_input_node, bottom_input_node)
            offset = y - node.pos.y
            offset_children(node, offset=-offset)


def calculate_mid_point(a: bw_node.Node, b: bw_node.Node) -> float:
    x = (a.pos.x + b.pos.x) / 2
    y = (a.pos.y + b.pos.y) / 2

    return x, y


class AlignNoOverlapAverageCenter(PostAlignmentBehavior):

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

    def run(self, node: bw_node.Node):
        if len(node.input_nodes_in_same_chain) < 2:
            return

        top_input_node = node.input_nodes_in_same_chain[0]
        bottom_input_node = node.input_nodes_in_same_chain[-1]
        _, mid_point = calculate_mid_point(top_input_node, bottom_input_node)

        nodes_above, nodes_below = self._get_input_nodes_around_point(
            node,
            mid_point
        )
        nodes_above.reverse()

        for input_node in nodes_above:
            align = AlignChainAboveSibling()
            align.run(input_node, node)

        for input_node in nodes_below:
            align = AlignChainBelowSibling()
            align.run(input_node, node)

        align = AlignInputsToCenter()
        align.run(node)
    

class InputNodeAlignmentBehavior(ABC):
    """
    Defines the behavior for positioning a single input node relative
    to a connected output noode.

    You must reimplement the run method with the logic for positioning
    the node.
    
    You must pass in the input node, the connected output node and the
    index in which the input node connects into the output node
    """
    @abstractmethod
    def run(self, input_node: bw_node.Node, output_node: bw_node.Node):
        pass

    @abstractmethod
    def get_sibling_node(self, input_node: bw_node.Node, output_node: bw_node.Node) -> bw_node.Node:
        pass


class NoInputNodeAlignment(InputNodeAlignmentBehavior):
    def run(self, input_node: bw_node.Node, output_node: bw_node.Node):
        pass

    def get_sibling_node(self, input_node: bw_node.Node, output_node: bw_node.Node) -> bw_node.Node:
        pass


class AlignLeftOutput(InputNodeAlignmentBehavior):
    def run(self, input_node: bw_node.Node, output_node: bw_node.Node):
        input_node.set_position(input_node.pos.x, output_node.pos.y)
    
    def get_sibling_node(self, input_node: bw_node.Node, output_node: bw_node.Node) -> bw_node.Node:
        pass


class AlignBelowSibling(InputNodeAlignmentBehavior):
    def run(self, input_node: bw_node.Node, output_node: bw_node.Node):
        node_above = self.get_sibling_node(input_node, output_node)
        try:
            cd = bw_chain_dimension.calculate_chain_dimension(
                node_above,
                input_node.chain,
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
    
    def get_sibling_node(self, input_node: bw_node.Node, output_node: bw_node.Node) -> bw_node.Node:
        i = get_index_in_input_list(input_node, output_node)
        return output_node.input_nodes_in_same_chain[i - 1]


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

    def get_sibling_node(self, input_node: bw_node.Node, output_node: bw_node.Node) -> bw_node.Node:
        i = get_index_in_input_list(input_node, output_node)
        return output_node.input_nodes_in_same_chain[i + 1]


class ChainAlignBehavior(InputNodeAlignmentBehavior, ABC):
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

        input_node.set_position(input_node.pos.x,
                                input_node.pos.y + offset)
        offset_children(input_node, offset=offset)

    @abstractmethod
    def calculate_offset(self,
                         input_node: bw_node.Node,
                         sibling_node: bw_node.Node,
                         smallest_cd: bw_chain_dimension.ChainDimension,
                         chain: bw_node_selection.NodeChain
                         ) -> float:
        pass

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


class AlignChainBelowSibling(ChainAlignBehavior):
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

    def get_sibling_node(self, input_node: bw_node.Node, output_node: bw_node.Node) -> bw_node.Node:
        i = get_index_in_input_list(input_node, output_node)
        return output_node.input_nodes_in_same_chain[i - 1]


class AlignChainAboveSibling(ChainAlignBehavior):
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

    def get_sibling_node(self, input_node: bw_node.Node, output_node: bw_node.Node) -> bw_node.Node:
        i = get_index_in_input_list(input_node, output_node)
        return output_node.input_nodes_in_same_chain[i + 1]


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
    on_first_input_node: InputNodeAlignmentBehavior
    on_input_node: InputNodeAlignmentBehavior
    on_finished_input_nodes: PostAlignmentBehavior

    def run(self, node: bw_node.Node):
        for i, input_node in enumerate(node.input_nodes_in_same_chain):
            if i == 0:
                self.on_first_input_node.run(input_node, node)
            else:
                self.on_input_node.run(input_node, node)

            if len(input_node.input_nodes_in_same_chain) > 0:
                self.run(input_node)
        self.on_finished_input_nodes.run(node)


def populate_queue(node: bw_node.Node, queue_order: List[bw_node.Node]):
    queue_order.append(node)
    for input_node in node.input_nodes:
        populate_queue(input_node, queue_order)


def run(node_selection: bw_node_selection.NodeSelection):
    # TODO: Add option to reposition roots or not
    # TODO: Add option to align by main line
    for node_chain in node_selection.node_chains:
        if node_chain.root.output_node_count != 0:
            continue
        sort_nodes(node_chain.root)

    for i, node_chain in enumerate(node_selection.node_chains):
        aligner = InputNodeAligner(
            on_first_input_node=AlignLeftOutput(),
            on_input_node=AlignBelowSibling(),
            on_finished_input_nodes=AlignInputsToCenter()
        )
        aligner.run(node_chain.root)

        original_pos = node_chain.root.pos.y
        aligner = InputNodeAligner(
            on_first_input_node=NoInputNodeAlignment(),
            on_input_node=NoInputNodeAlignment(),
            on_finished_input_nodes=AlignNoOverlapAverageCenter()
        )
        aligner.run(node_chain.root)

        # move back
        offset = original_pos - node_chain.root.pos.y
        node_chain.root.set_position(node_chain.root.pos.x, node_chain.root.pos.y + offset)
        offset_children(node_chain.root, offset)



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

def offset_children(parent_node: bw_node.Node, offset: float):
    for input_node in parent_node.input_nodes_in_same_chain:
        input_node.set_position(input_node.pos.x, input_node.pos.y + offset)
        offset_children(input_node, offset)


def get_index_in_input_list(input_node: bw_node.Node, output_node: bw_node.Node) -> int:
    for i, node in enumerate(output_node.input_nodes_in_same_chain):
        if node == input_node:
            return i


