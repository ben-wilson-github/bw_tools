from dataclasses import dataclass

from typing import List
from typing import Tuple

from common import bw_chain_dimension, bw_node
from . import input_alignment_behavior as iab
from . import post_alignment_behavior as pab
from . import utils

SPACER = 32

@dataclass
class ChainAligner():
    def run(self, node: bw_node.Node, seen: List[bw_node.Node]):
        input_node: bw_node.Node
        for input_node in node.input_nodes:
            if not input_node.is_root or input_node in seen:
                self.run(input_node, seen)
            else:
                self.do_something(input_node, node, seen)

    def do_something(self, node: bw_node.Node, output_node: bw_node.Node, seen: List[bw_node.Node]):
        print('============================')
        print(f'gonna do something with {node}')
        print(f'coming from {output_node}')
        # if node.identifier == 1419544088:
        #     return

        output_nodes = self._get_output_nodes_with_multiple_outputs(node)
        output_nodes.sort(key=lambda node: node.pos.x, reverse=True)
        print(f'Found output nodes with multiple inputs: {output_nodes}')
        if not output_nodes:
            print('Moving to mid point')
            _, y = utils.calculate_mid_point(node.output_nodes[0], node.output_nodes[-1])
            node.set_position(node.pos.x, y)
            node.update_offset_to_node(node.offset_node)
            node.refresh_positions_in_chain()
            return

        for i, output_node in enumerate(output_nodes):
            if i == 0:
                print(f'This is first time running')
                self._on_first_output_node(node, output_node)
            else:
                # run output node
                pass

        top_right_output = output_nodes[0]  # Aligning to this is gives us the straighest lines visually
        print(f'Done with work on outputs. Now align all the inputs for {top_right_output}')
        pab.average_positions_relative_to_node(top_right_output.input_nodes, top_right_output)

        print(f'Updating offset data')
        # Update input nodes offset data
        input_node: bw_node.Node
        print(top_right_output.input_nodes)
        for input_node in top_right_output.input_nodes:
            input_node.update_offset_to_node(top_right_output)
            print(f'Refreshing positions for {input_node}')
            input_node.refresh_positions_in_chain()

        for chain_root in seen:
            print(f'Also refreshing chain, because we already processed it {chain_root}')
            chain_root.refresh_positions_in_chain()

        seen.append(node)

    def _on_first_output_node(self,
                              node: bw_node.Node,
                              output_node: bw_node.Node):
        node_above, node_below = self._get_immediate_siblings(
            node,
            output_node
        )
        if node_above is not None and node_below is not None:
            print(f'node {node.label} is in between {node_above} and {node_below}')
            iab.align_node_between(node, node_above, node_below)
        elif node_below is not None:    # Input is above
            print(f'Gonna move above chain for {node_below}')
            node_below_cd = bw_chain_dimension.calculate_chain_dimension(node_below, node_below.chain, limit_bounds=bw_chain_dimension.Bound(left=node.pos.x))
            lower_bound = node.pos.y + node.height / 2
            upper_bound = node_below_cd.bounds.upper - SPACER
            iab.align_above_bound(node, lower_bound, upper_bound)
        else:   # Input is below
            print(f'Gonna move below chain for {node_above}')
            node_above_cd = bw_chain_dimension.calculate_chain_dimension(node_above, node_above.chain, limit_bounds=bw_chain_dimension.Bound(left=node.pos.x))
            lower_bound = node_above_cd.bounds.lower + SPACER
            upper_bound = node.pos.y - node.height / 2
            iab.align_below_bound(node, lower_bound, upper_bound)
             
    def _get_output_nodes_with_multiple_outputs(self,
                                                node: bw_node.Node
                                                ) -> List[bw_node.Node]:
        nodes = list()
        for output_node in node.output_nodes:
            if output_node.input_node_count >= 2:
                nodes.append(output_node)
        return nodes

    def _get_immediate_siblings(self,
                                node: bw_node.Node,
                                output_node: bw_node.Node
                                ) -> Tuple[bw_node.Node, bw_node.Node]:
        for i, input_node in enumerate(output_node.input_nodes):
            if input_node != node:
                continue

            node_above = None
            node_below = None
            if i != 0:
                try:
                    node_above = output_node.input_nodes[i - 1]
                except IndexError:
                    pass

            try:
                node_below = output_node.input_nodes[i + 1]
            except IndexError:
                pass

        return node_above, node_below

# @dataclass
# class NodeChainAlign(ChainAligner):
#     on_output_node = 0
#     on_finished_output_nodes = 0