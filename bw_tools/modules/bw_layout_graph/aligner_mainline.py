from __future__ import annotations

from dataclasses import dataclass
from operator import attrgetter
from typing import TYPE_CHECKING, List, Optional

from bw_tools.common.bw_chain_dimension import (
    BWChainDimension,
    BWNotInChainError,
    calculate_chain_dimension,
)

if TYPE_CHECKING:
    from .bw_layout_graph import BWLayoutSettings
    from .layout_node import BWLayoutNode


@dataclass
class BWMainlineAligner:
    settings: BWLayoutSettings

    def run_mainline(
        self,
        branching_nodes: List[BWLayoutNode],
        branching_output_nodes: List[BWLayoutNode],
    ):
        branching_nodes.sort(key=lambda node: node.pos.x)
        branching_node: BWLayoutNode
        for branching_node in branching_nodes:
            self.push_back_mainline_ignoring_branching_output_nodes(branching_node)

        branching_output_nodes.sort(key=lambda node: node.pos.x)
        branching_output_nodes.reverse()
        for branching_output_node in branching_output_nodes:
            self.push_back_branching_output_node_behind_largest_chain(branching_output_node)

    def _remove_cd_within_threshold(self, cds: List[BWChainDimension], threshold: float) -> List[BWChainDimension]:
        for cd in cds.copy():
            if cd.left_node.pos.x < threshold:
                # If the deepest cd is already past the threshold
                # then we know its safe to move behind it
                break
            cds.remove(cd)
        return cds

    def push_back_branching_output_node_behind_largest_chain(
        self,
        branching_output_node: BWLayoutNode,
    ):
        """
        Pushes a branching output node behind the largest sibling chain
        from all of its output nodes.
        """
        branching_input_nodes = [n for n in branching_output_node.output_nodes if n.has_branching_inputs]
        if len(branching_input_nodes) == 0:
            return

        # get all the inputs for these nodes
        inputs = list()
        for branching_input_node in branching_input_nodes:
            inputs += [n for n in branching_input_node.input_nodes if n is not branching_output_node]
        left_bound = self.find_left_most_bound(inputs)
        if left_bound is None:
            return

        spacer = self.settings.node_spacing
        spacer += self.settings.mainline_additional_offset

        # position the branching output node behind longest chain
        if branching_output_node.pos.x > (left_bound - spacer - branching_output_node.width / 2):
            branching_output_node.set_position(
                left_bound - spacer - branching_output_node.width / 2,
                branching_output_node.farthest_output_nodes_in_x[0].pos.y,
            )
            branching_output_node.alignment_behavior.offset_node = branching_output_node.farthest_output_nodes_in_x[0]
            branching_output_node.alignment_behavior.update_offset(branching_output_node.pos)
            self.reposition_node(branching_output_node, reposition_if_branching_output=False)

    def push_back_mainline_ignoring_branching_output_nodes(
        self,
        branching_node: BWLayoutNode,
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

        # Get sibling inputs
        inputs = [n for n in branching_node.input_nodes if n is not mainline_node]

        # Sort the chain dimensions by left bound
        cds = self.get_chain_dimensions_ignore_branches(inputs)
        if len(cds) == 0:
            return None
        cds.sort(key=lambda cd: cd.bounds.left)

        # Remove any cds which are within threshold
        threshold = branching_node.pos.x - self.settings.mainline_min_threshold
        cds = self._remove_cd_within_threshold(cds, threshold)
        if len(cds) == 0:
            # If no relevant sibling chains remain, we will not move back
            return None

        # Move mainline behind the deepest sibling chain
        left_bound = cds[0].bounds.left
        spacer = self.settings.node_spacing
        spacer += self.settings.mainline_additional_offset
        mainline_node.set_position(
            left_bound - spacer - (mainline_node.width / 2),
            mainline_node.pos.y,
        )
        mainline_node.alignment_behavior.offset_node = mainline_node.farthest_output_nodes_in_x[0]
        mainline_node.alignment_behavior.update_offset(mainline_node.pos)
        self.reposition_node(mainline_node)

    def find_left_most_bound(self, node_list: List[BWLayoutNode]) -> Optional[float]:
        """
        Given a list of nodes, returns the left most bound from the
        nodes chain. A chain does not include branching outputs
        """
        cds = self.get_chain_dimensions_ignore_branches(node_list)
        if len(cds) == 0:
            return None

        cd: BWChainDimension = min(cds, key=attrgetter("bounds.left"))
        return cd.bounds.left

    def find_potential_mainline_nodes(self, node: BWLayoutNode) -> List[BWLayoutNode]:
        """
        Returns a list of potentional mainline nodes from the given
        nodes inputs. If any of the nodes have branching outputs
        they are considered as mainline candidates, otherwise consider
        all inputs. The potential mainline nodes will be the ones farthest
        back.
        """
        potential_nodes: List[BWLayoutNode] = list()

        # Limit the list to branching nodes if possible
        potential_nodes = [n for n in node.input_nodes if n.has_branching_outputs]
        if not potential_nodes:
            potential_nodes = list(node.input_nodes)

        min_node = min(potential_nodes, key=attrgetter("pos.x"))
        potential_nodes = [n for n in potential_nodes if n.pos.x == min_node.pos.x]
        return potential_nodes

    def find_mainline_node(self, node: BWLayoutNode) -> Optional[BWLayoutNode]:
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

        cds: List[BWChainDimension] = self.get_chain_dimensions_for_inputs(node)
        if len(cds) == 0:
            return None

        # Fine the deepest chain
        min_cd = min(cds, key=attrgetter("bounds.left"))
        chains_of_same_size = [cd for cd in cds if cd.bounds.left == min_cd.bounds.left]
        if len(chains_of_same_size) == 1:
            return min_cd.right_node
        else:
            # If multiple chains are the same length, declare no mainline
            return None

    def calculate_node_lists_for_inputs(
        self,
        output_node: BWLayoutNode,
    ) -> List[List[BWLayoutNode]]:
        """Returns a list of all the nodes in the given nodes input chain"""
        node_lists = list()
        input_node: BWLayoutNode
        for input_node in output_node.input_nodes:
            node_lists.append(self.get_input_nodes(input_node))
        return node_lists

    def get_chain_dimensions_ignore_branches(
        self,
        nodes: List[BWLayoutNode],
    ) -> List[BWChainDimension]:
        cds = list()
        for node in nodes:
            node_list = self.get_input_nodes_ignore_branches(node)
            try:
                cd = calculate_chain_dimension(node, node_list)
            except BWNotInChainError:
                continue
            cds.append(cd)
        return cds

    def get_chain_dimensions_for_inputs(
        self,
        output_node: BWLayoutNode,
    ) -> List[BWChainDimension]:
        """
        Returns a list of chain dimensions for each connected input.
        """
        node_lists = self.calculate_node_lists_for_inputs(output_node)
        # if len(node_lists) < 2:
        #     return []

        cds = list()
        for i, input_node in enumerate(output_node.input_nodes):
            cd = calculate_chain_dimension(input_node, node_lists[i])
            cds.append(cd)
        return cds

    def reposition_branching_output_node(self, node: BWLayoutNode):
        spacer = self.settings.node_spacing
        spacer += self.settings.mainline_additional_offset
        new_x = (
            node.closest_output_node_in_x.pos.x - (node.closest_output_node_in_x.width / 2) - spacer - (node.width / 2)
        )
        node.set_position(new_x, node.farthest_output_nodes_in_x[0].pos.y)
        node.alignment_behavior.offset_node = node.farthest_output_nodes_in_x[0]
        node.alignment_behavior.update_offset(node.pos)

    def reposition_node(self, node: BWLayoutNode, reposition_if_branching_output=True):
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
    def get_input_nodes_ignore_branches(node: BWLayoutNode):
        def _populate_chain(node: BWLayoutNode):
            input_node: BWLayoutNode
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
    def get_input_nodes(node: BWLayoutNode):
        def _populate_chain(node: BWLayoutNode):
            input_node: BWLayoutNode
            for input_node in node.input_nodes:
                if input_node not in chain:
                    chain.append(input_node)
                _populate_chain(input_node)

        chain = [node]
        _populate_chain(node)
        return chain
