from __future__ import annotations, unicode_literals

from typing import TYPE_CHECKING, Optional, Tuple

from bw_tools.common.bw_api_tool import (
    SDConnection,
    SDNode,
    SDProperty,
    SDSBSCompGraph,
)
from sd.api.sdproperty import SDPropertyCategory

if TYPE_CHECKING:
    from bw_tools.common.bw_node import Node


def input_properties_match(node: Node, other: Node) -> bool:
    for other_property in other.api_node.getProperties(
        SDPropertyCategory.Input
    ):
        node_property = _get_matching_property(node, other_property)
        if node_property is None:
            return

        if _has_exposed_graph(node, node_property) or _has_exposed_graph(
            other, other_property
        ):
            return

        if node_property.isConnectable():
            if not _has_same_inputs(node, other, node_property, other_property):
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
        return

    nodes, other_nodes = _get_connected_nodes_from_connections(
        node_connections, other_connections
    )
    if any(
        nodes[i].getIdentifier() != other_nodes[i].getIdentifier()
        for i in range(len(nodes))
    ):
        return
    return True


def _get_matching_property(
    node: Node, property: SDProperty
) -> Optional[SDProperty]:
    # try:
    #     node_property = node.api_node.getPropertyFromId(other_property.getId(), SDPropertyCategory.Input)
    # except AttributeError:
    #     return False
    node_property = node.api_node.getPropertyFromId(
        property.getId(), SDPropertyCategory.Input
    )
    if node_property:
        return node_property
    return None


def _has_exposed_graph(node: Node, property: SDProperty) -> bool:
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
    return tuple(connected_nodes, other_connected_nodes)


def _values_match(node: Node, other_node: Node, property: SDProperty) -> bool:
    value = node.api_node.getInputPropertyValueFromId(property.getId()).get()
    other_value = other_node.api_node.getInputPropertyValueFromId(
        property.getId()
    ).get()
    return str(value) == str(other_value)
    # # Then make sure the values match
    # try:
    #     nodeValue = aNode.getInputPropertyValueFromId(other_property.getId()).get()
    #     uniqueNodeValue = other.getInputPropertyValueFromId(other_property.getId()).get()
    # except OSError as e:
    #     return False
    # except AttributeError:
    #     continue
    # else:
    #     if str(nodeValue) != str(uniqueNodeValue):
    #         return False
