from __future__ import annotations
from dataclasses import dataclass

from operator import attrgetter
from typing import TYPE_CHECKING, List, Optional

from bw_tools.common import bw_chain_dimension

if TYPE_CHECKING:
    from .bw_layout_graph import LayoutSettings
    from .layout_node import LayoutNode

MIN_CHAIN_SIZE = 96


@dataclass
class MainlineAligner:
    settings: LayoutSettings

    def run_mainline(
        self,
        branching_nodes: List[LayoutNode],
        branching_output_nodes: List[LayoutNode],
    ):
        branching_nodes.sort(key=lambda node: node.pos.x)
        branching_node: LayoutNode
        for branching_node in branching_nodes:
            self.push_back_mainline_ignoring_branching_output_nodes(
                branching_node
            )

        # TODO: make this an option too
        branching_output_nodes.sort(key=lambda node: node.pos.x)
        branching_output_nodes.reverse()
        for branching_output_node in branching_output_nodes:
            self.push_back_branching_output_node_behind_largest_chain(
                branching_output_node
            )

    def push_back_branching_output_node_behind_largest_chain(
        self,
        branching_output_node: LayoutNode,
    ):
        """
        Pushes a branching output node behind the largest sibling chain
        from all of its output nodes.
        """
        branching_input_nodes = [
            n
            for n in branching_output_node.output_nodes
            if n.has_branching_inputs
        ]
        if len(branching_input_nodes) == 0:
            return

        # get all the inputs for these nodes
        inputs = list()
        for branching_input_node in branching_input_nodes:
            inputs += [
                n
                for n in branching_input_node.input_nodes
                if n is not branching_output_node
            ]
        left_bound = self.find_left_most_bound(inputs)
        if left_bound is None:
            return

        spacer = self.settings.node_spacing
        spacer += self.settings.mainline_additional_offset

        # position the branching output node behind longest chain
        if branching_output_node.pos.x > (
            left_bound - spacer - branching_output_node.width / 2
        ):
            branching_output_node.set_position(
                left_bound - spacer - branching_output_node.width / 2,
                branching_output_node.farthest_output_nodes_in_x[0].pos.y,
            )
            branching_output_node.alignment_behavior.offset_node = (
                branching_output_node.farthest_output_nodes_in_x[0]
            )
            branching_output_node.alignment_behavior.update_offset(
                branching_output_node.pos
            )
            self.reposition_node(
                branching_output_node, reposition_if_branching_output=False
            )

    def push_back_mainline_ignoring_branching_output_nodes(
        self,
        branching_node: LayoutNode,
    ):
        """
        Finds a mainline node from the given nodes inputs and
        moves behind the largest sibling chain. The mainline
        node is also repositioned up until the first branching
        output node
        """
        mainline_node = self.find_mainline_node(branching_node)
        if mainline_node is None or mainline_node.has_branching_outputs:
            # These are handled in pass 2
            return

        inputs = [
            n for n in branching_node.input_nodes if n is not mainline_node
        ]
        left_bound = self.find_left_most_bound(inputs)
        if left_bound is None:
            return

        spacer = self.settings.node_spacing
        spacer += self.settings.mainline_additional_offset
        mainline_node.set_position(
            left_bound - spacer - (mainline_node.width / 2),
            mainline_node.pos.y,
        )
        mainline_node.alignment_behavior.offset_node = (
            mainline_node.farthest_output_nodes_in_x[0]
        )
        mainline_node.alignment_behavior.update_offset(mainline_node.pos)
        self.reposition_node(mainline_node)

    def find_left_most_bound(
        self, node_list: List[LayoutNode]
    ) -> Optional[float]:
        """
        Given a list of nodes, returns the left most bound from the
        nodes chain. A chain does not include branching outputs
        """
        cds = self.get_chain_dimensions_ignore_branches(node_list)
        if len(cds) == 0:
            return None
        cd: bw_chain_dimension.BWChainDimension = min(
            cds, key=attrgetter("bounds.left")
        )
        return cd.bounds.left

    def find_potential_mainline_nodes(
        self, node: LayoutNode
    ) -> List[LayoutNode]:
        """
        Returns a list of potentional mainline nodes from the given
        nodes inputs. If any of the nodes have branching outputs
        they are considered as mainline candidates, otherwise consider
        all inputs. The potential mainline nodes will be the ones farthest
        back.
        """
        potential_nodes: List[LayoutNode] = list()

        # Limit the list to branching nodes if possible
        potential_nodes = [
            n for n in node.input_nodes if n.has_branching_outputs
        ]
        if not potential_nodes:
            potential_nodes = list(node.input_nodes)

        min_node = min(potential_nodes, key=attrgetter("pos.x"))
        potential_nodes = [
            n for n in potential_nodes if n.pos.x == min_node.pos.x
        ]
        return potential_nodes

    def find_mainline_node(self, node: LayoutNode) -> LayoutNode:
        """
        Returns a mainline node from a given nodes potential mainline inputs.
        The node with the largest chain network will be considered mainline.
        If more than one node has the same chain size, the chain's node count
        is used instead.
        If all nodes have the same chain size and node count, the top most
        input is choosen.
        """
        potential_mainline_nodes = self.find_potential_mainline_nodes(node)
        if len(potential_mainline_nodes) == 1:
            return potential_mainline_nodes[0]

        cds: List[
            bw_chain_dimension.BWChainDimension
        ] = self.get_chain_dimensions_for_inputs(node)

        # For pleasing visual, do not consider chains
        # which are very small.
        for cd in cds.copy():
            if cd.width <= self.settings.mainline_min_threshold:
                cds.remove(cd)
        if len(cds) == 0:
            return None

        min_cd = min(cds, key=attrgetter("bounds.left"))

        chains_of_same_size = [
            cd for cd in cds if cd.bounds.left == min_cd.bounds.left
        ]

        mainline_chain = min(chains_of_same_size, key=attrgetter("node_count"))

        return mainline_chain.right_node

    def calculate_node_lists_for_inputs(
        self,
        output_node: LayoutNode,
    ) -> List[List[LayoutNode]]:
        """Returns a list of all the nodes in the given nodes input chain"""
        node_lists = list()
        input_node: LayoutNode
        for input_node in output_node.input_nodes:
            node_lists.append(self.get_input_nodes(input_node))
        return node_lists

    def get_chain_dimensions_ignore_branches(
        self,
        nodes: List[LayoutNode],
    ) -> List[bw_chain_dimension.BWChainDimension]:
        cds = list()
        for node in nodes:
            node_list = self.get_input_nodes_ignore_branches(node)
            try:
                cd = bw_chain_dimension.calculate_chain_dimension(
                    node, node_list
                )
            except bw_chain_dimension.BWNotInChainError:
                continue
            cds.append(cd)
        return cds

    def get_chain_dimensions_for_inputs(
        self,
        output_node: LayoutNode,
    ) -> List[bw_chain_dimension.BWChainDimension]:
        node_lists = self.calculate_node_lists_for_inputs(output_node)
        if len(node_lists) < 2:
            return []

        cds = list()
        for i, input_node in enumerate(output_node.input_nodes):
            cd = bw_chain_dimension.calculate_chain_dimension(
                input_node, node_lists[i]
            )
            cds.append(cd)
        return cds

    def reposition_branching_output_node(self, node: LayoutNode):
        spacer = self.settings.node_spacing
        spacer += self.settings.mainline_additional_offset
        new_x = (
            node.closest_output_node_in_x.pos.x
            - (node.closest_output_node_in_x.width / 2)
            - spacer
            - (node.width / 2)
        )
        node.set_position(new_x, node.farthest_output_nodes_in_x[0].pos.y)
        node.alignment_behavior.offset_node = node.farthest_output_nodes_in_x[
            0
        ]
        node.alignment_behavior.update_offset(node.pos)

    def reposition_node(
        self, node: LayoutNode, reposition_if_branching_output=True
    ):
        node.alignment_behavior.exec()

        inputs = list(node.input_nodes)
        if node.has_branching_outputs and reposition_if_branching_output:
            self.reposition_branching_output_node(node)

        if node.has_branching_inputs:
            mainline_node = self.find_mainline_node(node)
            if mainline_node is not None:
                # place mainline at the end of the list
                inputs.append(inputs.pop(inputs.index(mainline_node)))

        for input_node in inputs:
            self.reposition_node(input_node)

    @staticmethod
    def get_input_nodes_ignore_branches(node: LayoutNode):
        def _populate_chain(node: LayoutNode):
            input_node: LayoutNode
            for input_node in node.input_nodes:
                if input_node.has_branching_outputs:
                    continue
                if input_node not in chain:
                    chain.append(input_node)
                _populate_chain(input_node)

        if node.has_branching_outputs:
            return []
        chain = [node]
        _populate_chain(node)
        return chain

    @staticmethod
    def get_input_nodes(node: LayoutNode):
        def _populate_chain(node: LayoutNode):
            input_node: LayoutNode
            for input_node in node.input_nodes:
                if input_node not in chain:
                    chain.append(input_node)
                _populate_chain(input_node)

        chain = [node]
        _populate_chain(node)
        return chain
