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


class AllInputsAlignment(ABC):
    @abstractmethod
    def run(self, node: bw_node.Node):
        pass


class NoAlignmentAction(AllInputsAlignment):
    def run(self, node: bw_node.Node):
        pass


class AlignChildrenToBottom(AllInputsAlignment):
    def run(self, node: bw_node.Node):
        if len(node.input_nodes_in_same_chain) > 1:
            bottom_input_node = node.input_nodes_in_same_chain[-1]

            offset = bottom_input_node.pos.y - node.pos.y
            seen = []
            offset_children(node, offset=-offset, seen=seen)


class AlignChildrenToCenter(AllInputsAlignment):
    def run(self, node: bw_node.Node):
        if len(node.input_nodes_in_same_chain) > 1:
            top_input_node = node.input_nodes_in_same_chain[0]
            bottom_input_node = node.input_nodes_in_same_chain[-1]

            _, y = self.calculate_mid_point(top_input_node, bottom_input_node)
            offset = y - node.pos.y
            seen = []
            offset_children(node, offset=-offset, seen=seen)

    @staticmethod
    def calculate_mid_point(a: bw_node.Node, b: bw_node.Node) -> float:
        x = (a.pos.x + b.pos.x) / 2
        y = (a.pos.y + b.pos.y) / 2

        return x, y


class SingleInputAlignment(ABC):
    @abstractmethod
    def run(self, node: bw_node.Node, target_node: bw_node.Node, index: int):
        pass


class AlignLeftOutput(SingleInputAlignment):
    def run(self, node: bw_node.Node, output_node: bw_node.Node, _):
        node.set_position(node.pos.x, output_node.pos.y)


class AlignBelowSibling(SingleInputAlignment):
    def run(self, node: bw_node.Node, output_node: bw_node.Node, index: int):
        try:
            node_above = output_node.input_nodes_in_same_chain[index - 1]
            cd = bw_chain_dimension.calculate_chain_dimension(
                node_above,
                node.chain,
                limit_bounds=bw_chain_dimension.Bound(
                    left=node.pos.x
                )
            )
        except bw_chain_dimension.OutOfBoundsError:
            # The node above might be outside of the bounds
            # so this will fail. This can happen if the
            # input node outputs to the same parent more than
            # once
            pass
        else:
            new_pos_y = cd.bounds.lower + SPACER + node.height / 2
            node.set_position(node.pos.x, new_pos_y)


class AlignAboveSibling(SingleInputAlignment):
    def run(self, source_node: bw_node.Node, target_node: bw_node.Node):
        try:
            cd = bw_chain_dimension.calculate_chain_dimension(
                target_node,
                source_node.chain,
                limit_bounds=bw_chain_dimension.Bound(
                    left=source_node.pos.x
                )
            )
        except bw_chain_dimension.OutOfBoundsError:
            pass
        else:
            new_pos_y = cd.bounds.upper - SPACER - source_node.height / 2
            source_node.set_position(source_node.pos.x, new_pos_y)


class NodeAligner(ABC):
    on_first_input: SingleInputAlignment
    on_input: SingleInputAlignment
    on_finish: SingleInputAlignment

    def run(self, node: bw_node.Node):
        for i, input_node in enumerate(node.input_nodes_in_same_chain):
            if i == 0:
                self.on_first_input.run(input_node, node, i)
            else:
                self.on_input.run(input_node, node, i)

            if len(input_node.input_nodes_in_same_chain) >= 1:
                self.run(input_node)

        self.on_finish.run(node)


class StackAlignTop(NodeAligner):
    on_first_input = AlignLeftOutput()
    on_input = AlignBelowSibling()
    on_finish = NoAlignmentAction()


class StackAlignBottom(NodeAligner):
    on_first_input = AlignLeftOutput()
    on_input = AlignBelowSibling()
    on_finish = AlignChildrenToBottom()


class StackAlignCenter(NodeAligner):
    on_first_input = AlignLeftOutput()
    on_input = AlignBelowSibling()
    on_finish = AlignChildrenToCenter()


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
        # align = StackAlignTop()
        # align = StackAlignBottom()
        align = StackAlignCenter()
        align.run(node_chain.root)

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


def remove_overlap_in_children(parent_node: bw_node.Node):
    do_align = False
    for i, input_node in enumerate(parent_node.input_nodes_in_same_chain):
        if len(input_node.input_nodes_in_same_chain) > 1:
            remove_overlap_in_children(input_node)

        if i >= 1:
            node_above = parent_node.input_nodes_in_same_chain[i - 1]

            smallest_cd = calculate_smallest_chain_dimension(
                input_node,
                node_above,
                parent_node.chain
            )

            # caluclate chain dimension to find node at highest relevant node
            # from the input chain
            try:
                input_cd = bw_chain_dimension.calculate_chain_dimension(
                    input_node,
                    parent_node.chain,
                    limit_bounds=bw_chain_dimension.Bound(
                        left=smallest_cd.bounds.left
                    )
                )
            except bw_chain_dimension.OutOfBoundsError:
                highest_node = input_node
                input_high_bound = input_node.pos.y - input_node.height / 2
            else:
                highest_node = input_cd.upper_node
                input_high_bound = input_cd.bounds.upper

            try:
                # calculate chain dimension to find lowest relevant bound
                above_cd = bw_chain_dimension.calculate_chain_dimension(
                    node_above,
                    parent_node.chain,
                    limit_bounds=bw_chain_dimension.Bound(
                        left=highest_node.pos.x
                    )
                )
            except bw_chain_dimension.OutOfBoundsError:
                above_low_bound = node_above.pos.y + node_above.height / 2
            else:
                above_low_bound = above_cd.bounds.lower

            offset = (above_low_bound + SPACER) - input_high_bound
            seen = []
            offset_children(input_node, offset=offset, seen=seen)
            input_node.set_position(input_node.pos.x,
                                    input_node.pos.y + offset)
            do_align = True

    if do_align:
        strategy = AlignToInputsCenter()
        strategy.align(parent_node)

     
def offset_children(parent_node: bw_node.Node, offset: float, seen: List[bw_node.Node]):
    for input_node in parent_node.input_nodes_in_same_chain:
        if input_node in seen:
            continue

        input_node.set_position(input_node.pos.x, input_node.pos.y + offset)
        seen.append(input_node)
        offset_children(input_node, offset, seen)

def calculate_smallest_chain_dimension(a: bw_node.Node,
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
