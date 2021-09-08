from __future__ import annotations, unicode_literals

from typing import TYPE_CHECKING, Optional, Tuple

from bw_tools.common.bw_api_tool import (
    SDConnection,
    SDGraph,
    SDNode,
    SDProperty,
)
from sd.api.sdproperty import SDPropertyCategory

if TYPE_CHECKING:
    from bw_tools.common.bw_node import Node


def input_properties_match(node: Node, other: Node) -> bool:
    for other_property in other.api_node.getProperties(
        SDPropertyCategory.Input
    ):
        node_property = get_matching_input_property(node, other_property)
        if node_property is None:
            return

        if (
            _get_exposed_graph(node, node_property) is not None
            or _get_exposed_graph(other, other_property) is not None
        ):
            return

        if node_property.isConnectable():
            if not _has_same_inputs(
                node, other, node_property, other_property
            ):
                return

        if not _values_match(node, other, other_property):
            return

    # All the properties match, so these two nodes are the same
    return True


def _has_same_inputs(
    node: Node,
    other: Node,
    node_property: SDProperty,
    other_property: SDProperty,
) -> bool:
    node_connections = node.api_node.getPropertyConnections(node_property)
    other_connections = other.api_node.getPropertyConnections(other_property)
    if not _connection_counts_match(node_connections, other_connections):
        return False

    nodes, other_nodes = _get_connected_nodes_from_connections(
        node_connections, other_connections
    )
    if any(
        nodes[i].getIdentifier() != other_nodes[i].getIdentifier()
        for i in range(len(nodes))
    ):
        return False
    return True


def get_matching_input_property(
    node: Node, property: SDProperty
) -> Optional[SDProperty]:
    return _get_matching_property(node, property, SDPropertyCategory.Input)


def get_matching_output_property(
    node: Node, property: SDProperty
) -> Optional[SDProperty]:
    return _get_matching_property(node, property, SDPropertyCategory.Output)


def _get_matching_property(
    node: Node, property: SDProperty, category: SDPropertyCategory
) -> Optional[SDProperty]:
    node_property = node.api_node.getPropertyFromId(property.getId(), category)
    if node_property:
        return node_property
    return None


def _get_exposed_graph(node: Node, property: SDProperty) -> Optional[SDGraph]:
    return node.api_node.getPropertyGraph(property)


def _connection_counts_match(
    connection: SDConnection, other: SDConnection
) -> bool:
    return len(connection) == len(other)


def _get_connected_nodes_from_connections(
    node_connections: SDConnection, other_connections: SDConnection
) -> Tuple[Tuple[SDNode], Tuple[SDNode]]:
    connected_nodes = list()
    other_connected_nodes = list()

    for i in range(len(node_connections)):
        connected_nodes.append(node_connections[i].getInputPropertyNode())
        other_connected_nodes.append(
            other_connections[i].getInputPropertyNode()
        )
    return tuple(connected_nodes), tuple(other_connected_nodes)


def _values_match(node: Node, other_node: Node, property: SDProperty) -> bool:
    value = node.api_node.getInputPropertyValueFromId(property.getId())
    if value is not None:
        value = value.get()

    other_value = other_node.api_node.getInputPropertyValueFromId(
        property.getId()
    )
    if other_value is not None:
        other_value = other_value.get()

    return str(value) == str(other_value)
