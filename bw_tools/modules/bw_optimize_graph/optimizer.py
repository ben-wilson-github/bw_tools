from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Dict, List, Optional

import sd
from sd.api.sdproperty import SDPropertyCategory, SDPropertyInheritanceMethod

from . import property_matcher

if TYPE_CHECKING:
    from bw_tools.common.bw_api_tool import NodeID
    from bw_tools.common.bw_node import Node
    from bw_tools.common.bw_node_selection import NodeSelection
    from .bw_optimize_graph import OptimizeSettings


@dataclass
class Optimizer:
    node_selection: NodeSelection
    settings: OptimizeSettings
    deleted_count: int = 0

    def delete_duplicate_nodes(self, node_dict: Dict[Node, List[Node]]):
        self.deleted_count = 0
        for identifier, duplicate_nodes in node_dict.items():
            unique_node = self.node_selection.node(identifier)
            for duplicate_node in duplicate_nodes:
                self._reconnect_output_connections(duplicate_node, unique_node)
                self.node_selection.api_graph.deleteNode(
                    duplicate_node.api_node
                )
                self.deleted_count += 1
                self.node_selection.remove_node(duplicate_node)

    def get_nodes(self, node_id: NodeID) -> List[Node]:
        return [
            node
            for node in self.node_selection.nodes
            if node.api_node.getDefinition().getId() == node_id.value
        ]

    def find_duplicates(self, nodes: List[Node]) -> Dict[Node, List[Node]]:
        """
        Returns a dictionary of unique nodes in the keys and a list of
        duplciate nodes which match the unique node.
        """
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
            if node.label != unique_node.label:
                continue
            if property_matcher.input_properties_match(node, unique_node):
                return unique_node
        return None

    @staticmethod
    def _reconnect_output_connections(duplicate_node: Node, unique_node: Node):
        for output_connection in duplicate_node.output_connections:
            source_property = property_matcher.get_matching_output_property(
                unique_node, output_connection.getOutputProperty()
            )
            unique_node.api_node.newPropertyConnection(
                source_property,
                output_connection.getInputPropertyNode(),
                output_connection.getInputProperty(),
            )

    @staticmethod
    def _set_output_size(node: Node, size: int):
        output_size_property = node.api_node.getPropertyFromId(
            "$outputsize", SDPropertyCategory.Input
        )
        node.api_node.setPropertyInheritanceMethod(
            output_size_property, SDPropertyInheritanceMethod.Absolute
        )
        node.api_node.setPropertyValue(
            output_size_property,
            sd.api.sdvalueint2.SDValueInt2.sNew(
                sd.api.sdbasetypes.int2(size, size)
            ),
        )

    @staticmethod
    def _set_connected_output_nodes_inheritance_method(
        node: Node, inheritance_method: SDPropertyInheritanceMethod
    ):
        for connection in node.output_connections:
            connected_node = connection.getInputPropertyNode()
            output_size_property = connected_node.getPropertyFromId(
                "$outputsize", SDPropertyCategory.Input
            )

            if (
                connected_node.getPropertyInheritanceMethod(
                    output_size_property
                )
                != SDPropertyInheritanceMethod.RelativeToInput
            ):
                continue

            connected_node.setPropertyInheritanceMethod(
                output_size_property,
                inheritance_method,
            )