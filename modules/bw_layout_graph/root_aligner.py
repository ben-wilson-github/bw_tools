
@dataclass
class NodeRootChainAligner():
    on_output_node = 0
    on_finished_output_nodes = 0

    def run(self, node: bw_node.Node, seen: List[bw_node.Node]):
        for i, input_node in enumerate(node.input_nodes()):
            if not input_node.is_root and input_node not in seen:
                self.run(input_node, seen)
                continue

            print(f'Working on {input_node}')
            # seen.append(input_node)

            output_nodes = self._get_output_nodes_with_multiple_outputs(
                input_node
            )
            output_nodes.sort(key=lambda node: node.pos.x, reverse=True)
            if not output_nodes:
                # Align all inputs to center
                return

            for i, output_node in enumerate(output_nodes):
                if i == 0:
                    self._on_first_output_node(input_node, output_node)
                else:
                    # run output node
                    pass
            
            a = pab.AlignInputsToCenter(limit_to_chain=False)
            a.run(output_nodes[0])

            for input_node in output_nodes[0].input_nodes(limit_to_chain=False):
                input_node.update_offset_data(node)
            
            node.refresh_position_using_offset(recursive=True, limit_to_chain=False)




        # node.refresh_positions_using_offset(recursive=True)
        
    
    
    def _on_first_output_node(self, input_node: bw_node.Node, output_node: bw_node.Node):
        node_above, node_below = self._get_immediate_siblings(
            input_node,
            output_node
        )
        if node_above is not None and node_below is not None:
            # in middle
            pass
        elif node_below is not None:    # Input is above
            a = iab.AlignAboveSibling(limit_to_chain=False)
            a.run(input_node, output_node)
        else:   # Input is below
            a = iab.AlignBelowSibling(limit_to_chain=False)
            # a.run(input_node, output_node)
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
        for i, input_node in enumerate(output_node.input_nodes()):
            if input_node != node:
                continue
            
            node_above = None
            node_below = None
            if i != 0:
                try:
                    node_above = output_node.input_nodes()[i - 1]
                except IndexError:
                    pass

            try:
                node_below = output_node.input_nodes()[i + 1]
            except IndexError:
                pass

        return node_above, node_below

@dataclass
class NodeChainAlign(NodeRootChainAligner):
    on_output_node = 0
    on_finished_output_nodes = 0