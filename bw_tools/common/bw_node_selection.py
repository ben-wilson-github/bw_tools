from abc import ABC
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Dict, List, Tuple, TypeVar, Union

import sd
from bw_tools.common.bw_node import (InputConnectionData, Node,
                                     OutputConnectionData)

SDNode = TypeVar("SDNode")
SDArray = TypeVar("SDArray")
SDSBSCompGraph = TypeVar("SDSBSCompGraph")


class NodeNotInSelectionError(KeyError):
    def __init__(self):
        super().__init__("Node not in selection")


@dataclass
class NodeGroupInterface(ABC):
    # Node list is a dictionary of identifier keys with
    # a Node object as value
    _node_list: Dict[int, Node] = field(init=False, default_factory=dict)

    @property
    def nodes(self) -> Tuple[Node]:
        """Returns a tuple of all nodes in the selection"""
        ret = []
        for node in self._node_list.values():
            ret.append(node)
        return tuple(ret)

    @property
    def node_count(self) -> int:
        return len(self._node_list)

    def node(self, identifier: Union[int, str]) -> Node:
        try:
            node = self._node_list[int(identifier)]
        except KeyError:
            raise NodeNotInSelectionError()
        return node

    def add_node(self, node: Node):
        self._node_list[node.identifier] = node

    def contains(self, node: Node) -> bool:
        try:
            node = self._node_list[node.identifier]
        except KeyError:
            return False
        else:
            return True


@dataclass()
class NodeSelection(NodeGroupInterface):
    """
    This class provides more detailed information about the selected API nodes.

    A hiararchy tree structure is built for the selection and nodes are
    categorized. The selection is then further broken down into a series of
    NodeChain objects.

    Nodes are converted into Node objects
    """

    api_nodes: List[SDNode] = field(repr=False)
    api_graph: SDSBSCompGraph = field(repr=False)

    def __post_init__(self):
        self._create_nodes()
        self._build_node_tree()

    def _sort_nodes(self):
        for node in self.nodes:
            if node.is_root:
                self.root_nodes.append(node)

            if node.is_dot:
                self.dot_nodes.append(node)

    def _create_nodes(self):
        for api_node in self.api_nodes:
            node = Node(api_node)
            self.add_node(node)

    def _build_node_tree(self):
        for identifier in self._node_list:
            node = self.node(identifier)
            self._add_input_nodes(node)
            self._add_output_nodes(node)

    def _add_input_nodes(self, node: Node):
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
            api_node = api_connections[0].getInputPropertyNode()
            try:
                input_node = self.node(api_node.getIdentifier())
            except NodeNotInSelectionError:
                pass
            else:
                connection = InputConnectionData(index_in_node, input_node)
                node.add_input_connection_data(connection)

    def _add_output_nodes(self, node: Node):
        for index_in_node, api_property in enumerate(
            node.output_connectable_properties
        ):
            connection_data = OutputConnectionData(index_in_node)

            api_connections = node.api_node.getPropertyConnections(
                api_property
            )
            for api_connection in api_connections:
                output_api_node = api_connection.getInputPropertyNode()
                api_identifier = output_api_node.getIdentifier()
                try:
                    output_node = self.node(api_identifier)
                except NodeNotInSelectionError:
                    pass
                else:
                    connection_data.add_node(output_node)

            if connection_data.nodes:
                node.offset_node = connection_data.nodes[0]
                node.add_output_connection_data(connection_data)


def remove_dot_nodes(node_selection: NodeGroupInterface) -> bool:
    """
    Removes all dot nodes in the selection
    """
    for dot_node in node_selection.dot_nodes:
        dot_node = dot_node.api_node

        # Get property the connection comes from
        dot_node_input_property = dot_node.getPropertyFromId(
            "input", sd.api.sdproperty.SDPropertyCategory.Input
        )
        dot_node_input_connection = dot_node.getPropertyConnections(
            dot_node_input_property
        )[0]

        output_node_property = dot_node_input_connection.getInputProperty()
        output_node = dot_node_input_connection.getInputPropertyNode()

        # Get property the connection goes too
        dot_node_output_property = dot_node.getPropertyFromId(
            "unique_filter_output", sd.api.sdproperty.SDPropertyCategory.Output
        )

        dot_node_output_connections = dot_node.getPropertyConnections(
            dot_node_output_property
        )
        for connection in dot_node_output_connections:
            input_node_property = connection.getInputProperty()
            input_node = connection.getInputPropertyNode()

            output_node.newPropertyConnectionFromId(
                output_node_property.getId(),
                input_node,
                input_node_property.getId(),
            )

        node_selection.api_graph.deleteNode(dot_node)
    return True