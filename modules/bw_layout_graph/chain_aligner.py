from dataclasses import dataclass

from typing import List
from typing import Tuple

from common import bw_chain_dimension, bw_node
from . import input_alignment_behavior as iab
from . import post_alignment_behavior as pab


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
        if not output_nodes:
            # Align all inputs to center
            return

        output_nodes.sort(key=lambda node: node.pos.x, reverse=True)
        print(f'Found output nodes with multiple inputs: {output_nodes}')

        for i, output_node in enumerate(output_nodes):
            if i == 0:
                print(f'This is first time running')
                self._on_first_output_node(node, output_node)
            else:
                # run output node
                pass

        top_right_output = output_nodes[0]
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

        if node.identifier == 1419649033:
            raise AttributeError()

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
            # TODO: Change to bound function
            iab.align_node_above_chain(node, node_below, bw_chain_dimension.Bound(left=node.pos.x))
        else:   # Input is below
            print(f'Gonna move below chain {output_node}')
            iab.align_node_below_chain(node, node_above, bw_chain_dimension.Bound(left=node.pos.x))

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