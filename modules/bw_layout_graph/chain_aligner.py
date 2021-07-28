from dataclasses import dataclass

from typing import List
from typing import Tuple

from common import bw_node
from . import input_alignment_behavior as iab
from . import post_alignment_behavior as pab


@dataclass
class ChainAligner():
    on_output_node = 0
    on_finished_output_nodes = 0

    def run(self, node: bw_node.Node):
        input_node: bw_node.Node
        for i, input_node in enumerate(node.input_nodes):
            if not input_node.is_root:
                self.run(input_node)
            else:
                self.do_something(input_node, node)

    def do_something(self, node: bw_node.Node, output_node: bw_node.Node):
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
        print(f'Found output nodes with multiple inputs: {output_node}')

        for i, output_node in enumerate(output_nodes):
            if i == 0:
                self._on_first_output_node(node, output_node)
            else:
                # run output node
                pass

        print(f'Done with work on outputs. Now align all the inputs for {output_nodes[0]}')
        a = pab.AlignInputsToCenterPointUpdateChain()
        a.run(output_nodes[0])

        if node.offset_node is not None:
            node.update_offset_to_node(node.offset_node)
        input_node: bw_node.Node
        for input_node in node.input_nodes:
            input_node.update_offset_to_node(node)


    def _on_first_output_node(self,
                              node: bw_node.Node,
                              output_node: bw_node.Node):
        node_above, node_below = self._get_immediate_siblings(
            node,
            output_node
        )
        if node_above is not None and node_below is not None:
            # in middle
            pass
        elif node_below is not None:    # Input is above
            print(f'Gonna move above {output_node}')
            a = iab.AlignAboveSibling()
            a.run(node, output_node)
        else:   # Input is below
            a = iab.AlignBelowSibling()
            a.run(node, output_node)
            pass

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