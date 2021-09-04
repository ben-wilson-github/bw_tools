from __future__ import annotations, unicode_literals
from dataclasses import dataclass
from enum import unique
from bw_tools.common.bw_api_tool import NodeID, SDSBSCompGraph
from typing import List, TYPE_CHECKING, Optional, Tuple, Dict
from sd.api.sdproperty import SDPropertyCategory, SDPropertyInheritanceMethod
from . import property_matcher

if TYPE_CHECKING:
    from bw_tools.common.bw_node import Node
    from bw_tools.common.bw_node_selection import NodeSelection


@dataclass
class Optimizer:
    node_selection: NodeSelection

    def _reconnect_output_connections(
        self, duplicate_node: Node, unique_node: Node
    ):
        for output_connection in duplicate_node.output_connections:
            source_property = property_matcher.get_matching_output_property(
                unique_node, output_connection.getOutputProperty()
            )
            unique_node.api_node.newPropertyConnection(
                source_property,
                output_connection.getInputPropertyNode(),
                output_connection.getInputProperty(),
            )

    def _find_duplicates(self, nodes: List[Node]) -> Dict[Node, List[Node]]:
        unique_nodes: Dict[Node, List[Node]] = dict()
        for node in nodes:
            duplicate_of: Node = self._is_duplicate_of_a_node(
                node, unique_nodes
            )

            if duplicate_of is None:
                unique_nodes[node.identifier] = list()
                continue

            unique_nodes[duplicate_of.identifier].append(node)
        return unique_nodes

    def _is_duplicate_of_a_node(
        self, node: Node, unique_nodes: Dict[Node, List[Node]]
    ) -> Optional(Node):
        for identifier in unique_nodes.keys():
            unique_node = self.node_selection.node(identifier)
            if property_matcher.input_properties_match(node, unique_node):
                return unique_node
        return None


@dataclass
class UniformOptimizer(Optimizer):
    def run(self):
        uniform_color_nodes = self._get_uniform_color_nodes()
        uniform_color_nodes.sort(key=lambda n: n.pos.x)
        node_dict = self._find_duplicates(uniform_color_nodes)
        for identifier, duplicate_nodes in node_dict.items():
            unique_node = self.node_selection.node(identifier)

            for duplicate_node in duplicate_nodes:
                self._reconnect_output_connections(duplicate_node, unique_node)
                self.node_selection.api_graph.deleteNode(duplicate_node.api_node)
            


    def _get_uniform_color_nodes(self) -> List[Node]:
        return [
            node
            for node in self.node_selection.nodes
            if node.api_node.getDefinition().getId()
            == NodeID.UNIFORM_COLOR.value
        ]


    @staticmethod
    def _set_output_size(node: Node, size: int):
        output_size_property = node.api_node.getPropertyFromId('$outputsize', SDPropertyCategory.Input)
        node.api_node.setPropertyInheritanceMethod(output_size_property, SDPropertyInheritanceMethod.Absolute)
        node.api_node.setPropertyValue(output_size_property, SDValueInt2.sNew(int2(size, size)))

    def optimizeUniformColor(self, node: Node):
        """
        Forces a uniform color node to 16x16 and sets any connected nodes to relativeToParent if
        they were not manually modified
        """
        self._set_output_size(node, 4)

        # Handle connected nodes
        output_property = node.api_node.getPropertyFromId('unique_filter_output', SDPropertyCategory.Output)
        for connection in node.output_connections:
            CONTINUE REFACTOR HERE
            # If we are able to get the connected node properties, then ignore it. Likely connected to an output node
            try:
                connectedNode = connection.getInputPropertyNode()
                connectedNodeOutputSizeProperty = connectedNode.getPropertyFromId('$outputsize', SDPropertyCategory.Input)
                connectedNodeInheritanceMethod = connectedNode.getPropertyInheritanceMethod(connectedNodeOutputSizeProperty)
            except AttributeError:
                continue
            else:
                # If relative to input, force to relative to parent
                if connectedNodeInheritanceMethod == SDPropertyInheritanceMethod.RelativeToInput:
                    connectedNode.setPropertyInheritanceMethod(connectedNodeOutputSizeProperty, SDPropertyInheritanceMethod.RelativeToParent)
