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
    def run(self, node: bw_node.Node):
        if len(node.input_nodes_in_same_chain) <= 1:
            return

        top_input_node = node.input_nodes_in_same_chain[0]
        bottom_input_node = node.input_nodes_in_same_chain[-1]
        _, mid_point = calculate_mid_point(top_input_node, bottom_input_node)

        for i, input_node in enumerate(node.input_nodes_in_same_chain):
            if input_node.pos.y < mid_point:
                align = AlignChainAboveSibling()
                align.run(input_node, node, i)
                return
            elif input_node.pos.y > mid_point:
                align = AlignChainBelowSibling()
                align.run(input_node, node, i)
            else:
                continue

        # align = AlignOutputToInputsCenter()
        # align.run(node)


class AlignOutputToInputsCenter(PostAlignmentBehavior):
    def run(self, node: bw_node.Node):
        if len(node.input_nodes_in_same_chain) > 1:
            top_input_node = node.input_nodes_in_same_chain[0]
            bottom_input_node = node.input_nodes_in_same_chain[-1]

            _, y = calculate_mid_point(top_input_node, bottom_input_node)
            offset = y - node.pos.y
            node.set_position(node.pos.x, y)
            self.offset_parents(node, offset)
    
    def offset_parents(self, node: bw_node.Node, offset: float):
        for output_node in node.output_nodes:
            output_node.set_position(output_node.pos.x, output_node.pos.y + offset)


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
    def run(self, input_node: bw_node.Node, output_node: bw_node.Node, index: int):
        pass


class NoInputNodeAlignment(InputNodeAlignmentBehavior):
    def run(self, input_node: bw_node.Node, output_node: bw_node.Node, index: int):
        pass


class AlignLeftOutput(InputNodeAlignmentBehavior):
    def run(self, input_node: bw_node.Node, output_node: bw_node.Node, _):
        input_node.set_position(input_node.pos.x, output_node.pos.y)


class AlignBelowSibling(InputNodeAlignmentBehavior):
    def run(self, input_node: bw_node.Node, output_node: bw_node.Node, index: int):
        node_above = output_node.input_nodes_in_same_chain[index - 1]

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


class AlignAboveSibling(InputNodeAlignmentBehavior):
    def run(self, input_node: bw_node.Node, output_node: bw_node.Node, index: int):
        if index < 1:
            return

        node_above = output_node.input_nodes_in_same_chain[index - 1]
        try:
            cd = bw_chain_dimension.calculate_chain_dimension(
                node_above,
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


class ChainAlignBehavior(InputNodeAlignmentBehavior, ABC):
    def run(self, input_node: bw_node.Node, output_node: bw_node.Node, index: int):
        sib_node = self.get_sibling_node(output_node, index)

        smallest_cd = self._calculate_smallest_chain_dimension(
            input_node,
            sib_node,
            output_node.chain
        )

        THINK I NEED TO FLIP THE ORDER OF THESE BOUNDS CHECKS FOR 
        ALIGNING UPPER OR LOWER
        # Get the input chain relevant bounds
        try:
            input_cd = bw_chain_dimension.calculate_chain_dimension(
                input_node,
                output_node.chain,
                limit_bounds=bw_chain_dimension.Bound(
                    left=smallest_cd.bounds.left
                )
            )
        except bw_chain_dimension.OutOfBoundsError:
            bound_x, bound_y = self.get_input_chain_bound_on_fail(input_node)
        else:
            bound_x, bound_y = self.get_input_chain_bound_on_pass(input_cd)

        # Get sibling chain relevant bounds
        try:
            sibling_cd = bw_chain_dimension.calculate_chain_dimension(
                sib_node,
                output_node.chain,
                limit_bounds=bw_chain_dimension.Bound(
                    left=bound_x
                )
            )
        except bw_chain_dimension.OutOfBoundsError:
            sibling_bound_y = self.get_sibling_chain_bound_on_fail(sib_node)
        else:
            sibling_bound_y = self.get_sibling_chain_bound_on_pass(sibling_cd)

        offset = self.calculate_offset(bound_y, sibling_bound_y)

        input_node.set_position(input_node.pos.x,
                                input_node.pos.y + offset)
        offset_children(input_node, offset=offset)

    @abstractmethod
    def get_sibling_node(self, output_node: bw_node.Node, index: int) -> bw_node.Node:
        pass

    @abstractmethod
    def calculate_offset(self,
                         input_bound: float,
                         sibling_bound: float
                         ) -> float:
        pass

    @abstractmethod
    def get_input_chain_bound_on_fail(self,
                                      input_node: bw_node.Node
                                      ) -> Tuple[float, float]:
        pass

    @abstractmethod
    def get_input_chain_bound_on_pass(self,
                                      cd: bw_chain_dimension.ChainDimension
                                      ) -> Tuple[float, float]:
        pass

    @abstractmethod
    def get_sibling_chain_bound_on_fail(self,
                                        sibling_node: bw_node.Node
                                        ) -> Tuple[float, float]:
        pass

    @abstractmethod
    def get_sibling_chain_bound_on_pass(self,
                                        cd: bw_chain_dimension.ChainDimension
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


class AlignChainBelowSibling(ChainAlignBehavior):
    def get_sibling_node(self, output_node: bw_node.Node, index: int) -> bw_node.Node:
        return output_node.input_nodes_in_same_chain[index - 1]
    
    def get_input_chain_bound_on_fail(self,
                                      input_node: bw_node.Node
                                      ) -> Tuple[float, float]:
        return input_node.pos.x, input_node.pos.y - input_node.height / 2
    
    def get_input_chain_bound_on_pass(self,
                                      cd: bw_chain_dimension.ChainDimension
                                      ) -> Tuple[float, float]:
        return cd.upper_node.pos.x, cd.bounds.upper

    def get_sibling_chain_bound_on_fail(self,
                                        sibling_node: bw_node.Node
                                        ) -> Tuple[float, float]:
        return sibling_node.pos.y + sibling_node.height / 2

    def get_sibling_chain_bound_on_pass(self,
                                        cd: bw_chain_dimension.ChainDimension
                                        ) -> float:
        return cd.bounds.lower

    def calculate_offset(self,
                         input_bound: float,
                         sibling_bound: float
                         ) -> float:
        return (sibling_bound + SPACER) - input_bound


class AlignChainAboveSibling(ChainAlignBehavior):
    def get_sibling_node(self, output_node: bw_node.Node, index: int) -> bw_node.Node:
        return output_node.input_nodes_in_same_chain[index + 1]

    def get_input_chain_bound_on_fail(self,
                                      input_node: bw_node.Node
                                      ) -> Tuple[float, float]:
        return input_node.pos.x, input_node.pos.y + input_node.height / 2

    def get_input_chain_bound_on_pass(self,
                                      cd: bw_chain_dimension.ChainDimension
                                      ) -> Tuple[float, float]:
        return cd.lower_node.pos.x, cd.bounds.lower

    def get_sibling_chain_bound_on_fail(self,
                                        sibling_node: bw_node.Node
                                        ) -> Tuple[float, float]:
        return sibling_node.pos.y - sibling_node.height / 2

    def get_sibling_chain_bound_on_pass(self,
                                        cd: bw_chain_dimension.ChainDimension
                                        ) -> float:
        return cd.bounds.upper

    def calculate_offset(self,
                         input_bound: float,
                         sibling_bound: float
                         ) -> float:
        return (sibling_bound - SPACER) - input_bound





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

    on_finished_alignment: PostAlignmentBehavior = Is called after the
    entire chain of the given node is processed. This is useful for 
    applying logic on the newly position chain. For example, by remove
    overlap left over from the alignment process.
    """
    on_first_input_node: InputNodeAlignmentBehavior
    on_input_node: InputNodeAlignmentBehavior
    on_finished_input_nodes: PostAlignmentBehavior
    # on_finished_alignment: PostAlignmentBehavior

    def run(self, node: bw_node.Node):
        self._run_align_on_input_nodes(node)
        # self.on_finished_alignment.run(node)

    def _run_align_on_input_nodes(self, node: bw_node.Node):
        for i, input_node in enumerate(node.input_nodes_in_same_chain):
            if i == 0:
                self.on_first_input_node.run(input_node, node, i)
            else:
                self.on_input_node.run(input_node, node, i)

            if len(input_node.input_nodes_in_same_chain) >= 1:
                self._run_align_on_input_nodes(input_node)
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

        # offset = original_pos - node_chain.root.pos.y
        # node_chain.root.set_position(node_chain.root.pos.x, node_chain.root.pos.y + offset)
        # offset_children(node_chain.root, offset)



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


def layout_y_axis(node: bw_node.Node):
    for i, input_node in enumerate(node.input_nodes_in_same_chain):
        if input_node.is_root:
            continue
        # Default position is inline with the parent
        # If there are multiple parents, the lowest one
        # will become the last one processed
        new_pos_y = node.pos.y
        if i != 0:
            node_above = node.input_nodes[i - 1]

            try:
                above_cd = bw_chain_dimension.calculate_chain_dimension(
                    node_above,
                    node.chain,
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
                new_pos_y = above_cd.bounds.lower + SPACER + input_node.height / 2

        input_node.set_position(input_node.pos.x, new_pos_y)

        if len(input_node.input_nodes_in_same_chain) >= 1:
            layout_y_axis(input_node)

    # if len(node.input_nodes_in_same_chain) > 1:
    #     strategy = AlignInputsToOutputCenter()
    #     strategy.align(node)


def _get_immediate_siblings(index: int,
                            parent_node: bw_node.Node
) -> Tuple[Union[bw_node.Node, None], Union[bw_node.Node, None]]:
    above_index = index - 1
    if index < 0:
        sibling_above = None
    else:
        sibling_above = parent_node.input_nodes_in_same_chain[above_index] 

    try: 
        sibling_below = parent_node.input_nodes_in_same_chain[index + 1]
    except IndexError:
        sibling_below = None

    return sibling_above, sibling_below    


def offset_children(parent_node: bw_node.Node, offset: float):
    for input_node in parent_node.input_nodes_in_same_chain:
        input_node.set_position(input_node.pos.x, input_node.pos.y + offset)
        offset_children(input_node, offset)


