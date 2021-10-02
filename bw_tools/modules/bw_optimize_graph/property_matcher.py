from __future__ import annotations, unicode_literals

from typing import TYPE_CHECKING, List, Optional, Tuple

from sd.api.sdconnection import SDConnection
from sd.api.sdgraph import SDGraph
from sd.api.sdnode import SDNode
from sd.api.sdproperty import SDProperty, SDPropertyCategory
from sd.api.sdvalue import SDValue

if TYPE_CHECKING:
    from bw_tools.common.bw_node import BWNode


def input_properties_match(node: BWNode, other: BWNode) -> bool:
    for other_property in other.api_node.getProperties(
        SDPropertyCategory.Input
    ):
        node_property = get_matching_input_property(node, other_property)
        if node_property is None:
            # If it was not possible to find a matching property
            # then the two nodes could not be duplicates
            return

        if (
            _get_exposed_graph(node, node_property) is not None
            or _get_exposed_graph(other, other_property) is not None
        ):
            # If either propety has a function graph attached, we
            # declare them as not duplicates
            return

        if node_property.isConnectable():
            # If the property is connectable,
            # then it must be of type SDTypeTexture
            if not _have_same_inputs(
                node, other, node_property, other_property
            ):
                return
        else:
            if not _values_match(node, other, other_property):
                return

    # All the properties match, so these two nodes are the same
    return True


def _have_same_inputs(
    node: BWNode,
    other: BWNode,
    node_property: SDProperty,
    other_property: SDProperty,
) -> bool:
    node_connections = node.api_node.getPropertyConnections(node_property)
    other_connections = other.api_node.getPropertyConnections(other_property)
    if not _connection_counts_match(node_connections, other_connections):
        # if they two nodes have different connection counts, they
        # must be different
        return False

    nodes, other_nodes = _get_connected_nodes_from_connections(
        node_connections, other_connections
    )

    if _have_different_input_nodes_connected(nodes, other_nodes):
        return False

    if _is_connected_to_different_input_property(
        node_connections, other_connections
    ):
        return False

    return True


def _is_connected_to_different_input_property(
    node_connections: List[SDConnection], other_connections: List[SDConnection]
):
    node_connected_properties: List[SDProperty] = [
        con.getInputProperty() for con in node_connections
    ]
    other_node_connected_properties: List[SDProperty] = [
        con.getInputProperty() for con in other_connections
    ]
    for np in node_connected_properties:
        for op in other_node_connected_properties:
            if np.getId() != op.getId():
                return True
    return False


def _have_different_input_nodes_connected(
    nodes: List[SDNode], other_nodes: List[SDNode]
):
    return any(
        nodes[i].getIdentifier() != other_nodes[i].getIdentifier()
        for i in range(len(nodes))
    )


def get_matching_input_property(
    node: BWNode, property: SDProperty
) -> Optional[SDProperty]:
    return _get_matching_property(node, property, SDPropertyCategory.Input)


def get_matching_output_property(
    node: BWNode, property: SDProperty
) -> Optional[SDProperty]:
    return _get_matching_property(node, property, SDPropertyCategory.Output)


def _get_matching_property(
    node: BWNode, property: SDProperty, category: SDPropertyCategory
) -> Optional[SDProperty]:
    node_property = node.api_node.getPropertyFromId(property.getId(), category)
    if node_property:
        return node_property
    return None


def _get_exposed_graph(
    node: BWNode, property: SDProperty
) -> Optional[SDGraph]:
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


def _values_match(
    node: BWNode, other_node: BWNode, property: SDProperty
) -> bool:
    value: SDValue = node.api_node.getInputPropertyValueFromId(
        property.getId()
    )
    # if value is not None:
    value = value.get()

    other_value = other_node.api_node.getInputPropertyValueFromId(
        property.getId()
    )
    # if other_value is not None:
    other_value = other_value.get()

    return str(value) == str(other_value)
