from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Dict, List, Optional

import sd
from sd.api.sdproperty import SDPropertyCategory, SDPropertyInheritanceMethod

from . import property_matcher
from bw_tools.common.bw_api_tool import CompNodeID

if TYPE_CHECKING:
    from bw_tools.common.bw_node import BWNode
    from bw_tools.common.bw_node_selection import BWNodeSelection

    from .bw_optimize_graph import BWOptimizeSettings


@dataclass
class Optimizer:
    node_selection: BWNodeSelection
    settings: BWOptimizeSettings
    deleted_count: int = 0

    def delete_duplicate_nodes(self, node_dict: Dict[BWNode, List[BWNode]]):
        self.deleted_count = 0
        for identifier, duplicate_nodes in node_dict.items():
            unique_node = self.node_selection.node(identifier)
            for duplicate_node in duplicate_nodes:
                self._reconnect_output_connections(duplicate_node, unique_node)
                self.node_selection.api_graph.deleteNode(duplicate_node.api_node)
                self.deleted_count += 1
                self.node_selection.remove_node(duplicate_node)

    def get_nodes(self, node_id: CompNodeID) -> List[BWNode]:
        return [node for node in self.node_selection.nodes if node.api_node.getDefinition().getId() == node_id.value]

    def find_duplicates(self, nodes: List[BWNode]) -> Dict[BWNode, List[BWNode]]:
        """
        Returns a dictionary of unique nodes in the keys and a list of
        duplciate nodes which match the unique node.
        """
        unique_nodes: Dict[BWNode, List[BWNode]] = dict()
        for node in nodes:
            duplicate_of: Optional[BWNode] = self._is_duplicate_of_a_node(node, unique_nodes)

            if duplicate_of is None:
                unique_nodes[node.identifier] = list()
                continue

            unique_nodes[duplicate_of.identifier].append(node)
        return unique_nodes

    def _is_duplicate_of_a_node(self, node: BWNode, unique_nodes: Dict[BWNode, List[BWNode]]) -> Optional(BWNode):
        """
        Given a potential duplicate node and a list of unique nodes, will
        return the unique node that the given node is a duplicate of.
        """
        for identifier in unique_nodes.keys():
            unique_node = self.node_selection.node(identifier)

            # If the labels do not match, the nodes could not possibly
            # be duplicates
            if node.label != unique_node.label:
                continue

            if property_matcher.input_properties_match(node, unique_node):
                return unique_node
        return None

    @staticmethod
    def _reconnect_output_connections(duplicate_node: BWNode, unique_node: BWNode):
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
    def _set_output_size(node: BWNode, size: int):
        output_size_property = node.api_node.getPropertyFromId("$outputsize", SDPropertyCategory.Input)
        node.api_node.setPropertyInheritanceMethod(output_size_property, SDPropertyInheritanceMethod.Absolute)
        node.api_node.setPropertyValue(
            output_size_property,
            sd.api.sdvalueint2.SDValueInt2.sNew(sd.api.sdbasetypes.int2(size, size)),
        )

    @staticmethod
    def _set_connected_output_nodes_inheritance_method(node: BWNode, inheritance_method: SDPropertyInheritanceMethod):
        for connection in node.output_connections:
            connected_node = connection.getInputPropertyNode()
            output_size_property = connected_node.getPropertyFromId("$outputsize", SDPropertyCategory.Input)

            # Ignore output nodes
            if connected_node.getDefinition().getId() == CompNodeID.OUTPUT.value:
                return

            if (
                connected_node.getPropertyInheritanceMethod(output_size_property)
                != SDPropertyInheritanceMethod.RelativeToInput
            ):
                continue

            connected_node.setPropertyInheritanceMethod(
                output_size_property,
                inheritance_method,
            )
