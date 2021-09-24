from abc import ABC
from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Union

from sd.api.sdconnection import SDConnection
from sd.api.sdgraph import SDGraph
from sd.api.sdnode import SDNode
from sd.api.sdproperty import SDProperty, SDPropertyCategory

from .bw_node import BWInputConnectionData, BWNode, BWOutputConnectionData


class BWNodeNotInSelectionError(KeyError):
    def __init__(self):
        super().__init__("Node not in selection")


@dataclass
class NodeGroupInterface(ABC):
    # Node list is a dictionary of identifier keys with
    # a Node object as value
    _node_list: Dict[int, BWNode] = field(init=False, default_factory=dict)

    @property
    def nodes(self) -> Tuple[BWNode]:
        """Returns a tuple of all nodes in the selection"""
        ret = []
        for node in self._node_list.values():
            ret.append(node)
        return tuple(ret)

    @property
    def node_count(self) -> int:
        return len(self._node_list)

    def node(self, identifier: Union[int, str]) -> BWNode:
        try:
            node = self._node_list[int(identifier)]
        except KeyError:
            raise BWNodeNotInSelectionError()
        return node

    def add_node(self, node: BWNode):
        self._node_list[node.identifier] = node

    def remove_node(self, node: BWNode):
        del self._node_list[node.identifier]

    def contains(self, node: BWNode) -> bool:
        try:
            node = self._node_list[node.identifier]
        except KeyError:
            return False
        else:
            return True


@dataclass()
class BWNodeSelection(NodeGroupInterface):
    """
    This class provides more detailed information about the selected API nodes.

    A hiararchy tree structure is built for the selection and nodes are
    categorized. The selection is then further broken down into a series of
    NodeChain objects.

    Nodes are converted into Node objects
    """

    api_nodes: List[SDNode] = field(repr=False)
    api_graph: SDGraph = field(repr=False)

    def __post_init__(self):
        self._create_nodes()
        self._build_node_tree()

    def _create_nodes(self):
        for api_node in self.api_nodes:
            node = BWNode(api_node)
            self.add_node(node)

    def _build_node_tree(self):
        for identifier in self._node_list:
            node = self.node(identifier)
            self._add_input_nodes(node)
            self._add_output_nodes(node)

    def _add_input_nodes(self, node: BWNode):
        for index_in_node, api_property in enumerate(
            node.input_connectable_properties
        ):
            api_connections = node.api_node.getPropertyConnections(
                api_property
            )
            if len(api_connections) == 0:
                continue

            # Because we are only looking at input properties. We can be sure
            # there will only be one connection or none at all. No need
            # to loop through all connections as there is only 1.
            api_node: SDNode = api_connections[0].getInputPropertyNode()
            try:
                input_node = self.node(api_node.getIdentifier())
            except BWNodeNotInSelectionError:
                pass
            else:
                connection = BWInputConnectionData(index_in_node, input_node)
                node.add_input_connection_data(connection)

    def _add_output_nodes(self, node: BWNode):
        for index_in_node, api_property in enumerate(
            node.output_connectable_properties
        ):
            connection_data = BWOutputConnectionData(index_in_node)

            api_connections = node.api_node.getPropertyConnections(
                api_property
            )
            api_connection: SDConnection
            for api_connection in api_connections:
                output_api_node: SDNode = api_connection.getInputPropertyNode()
                api_identifier = output_api_node.getIdentifier()
                try:
                    output_node = self.node(api_identifier)
                except BWNodeNotInSelectionError:
                    pass
                else:
                    connection_data.add_node(output_node)

            if connection_data.nodes:
                node.add_output_connection_data(connection_data)


def remove_dot_nodes(
    api_nodes: List[SDNode], api_graph: SDGraph
) -> List[SDNode]:
    """
    Removes all dot nodes in the selection
    """
    api_nodes = [n for n in api_nodes]
    dot_nodes = list()
    for api_node in api_nodes:
        if api_node.getDefinition().getId() != "sbs::compositing::passthrough":
            continue

        # Get property the connection comes from
        dot_node_input_property = api_node.getPropertyFromId(
            "input", SDPropertyCategory.Input
        )
        dot_node_input_connection: SDConnection = (
            api_node.getPropertyConnections(dot_node_input_property)[0]
        )

        output_node_property: SDProperty = (
            dot_node_input_connection.getInputProperty()
        )
        output_node: SDNode = dot_node_input_connection.getInputPropertyNode()

        # Get property the connection goes too
        dot_node_output_property = api_node.getPropertyFromId(
            "unique_filter_output", SDPropertyCategory.Output
        )

        dot_node_output_connections: SDConnection = (
            api_node.getPropertyConnections(dot_node_output_property)
        )
        connection: SDConnection
        for connection in dot_node_output_connections:
            input_node_property: SDProperty = connection.getInputProperty()
            input_node: SDNode = connection.getInputPropertyNode()

            output_node.newPropertyConnectionFromId(
                output_node_property.getId(),
                input_node,
                input_node_property.getId(),
            )

        api_graph.deleteNode(api_node)
        dot_nodes.append(api_node)

    api_nodes = [n for n in api_nodes if n not in dot_nodes]
    return api_nodes
