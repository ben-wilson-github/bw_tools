from abc import ABC, abstractmethod
import importlib

import sd

from dataclasses import dataclass
from dataclasses import field
from typing import List
from typing import Union
from typing import Tuple
from typing import TypeVar
from typing import Dict

from common import bw_node

importlib.reload(bw_node)


SDNode = TypeVar('SDNode')
SDArray = TypeVar('SDArray')
SDSBSCompGraph = TypeVar('SDSBSCompGraph')


class NodeNotInSelectionError(KeyError):
    def __init__(self):
        super().__init__('Node not in selection')


@dataclass
class NodeGroupInterface(ABC):
    # Node list is a dictionary of identifier keys with
    # a bw_node.Node object as value
    _node_list: Dict[int, bw_node.Node] = field(init=False, default_factory=dict)

    @property
    def nodes(self) -> Tuple[bw_node.Node]:
        """Returns a tuple of all nodes in the selection"""
        ret = []
        for node in self._node_list.values():
            ret.append(node)
        return tuple(ret)

    @property
    def node_count(self):
        return len(self._node_list)

    def node(self, identifier: Union[int, str]) -> bw_node.Node:
        try:
            node = self._node_list[int(identifier)]
        except KeyError:
            raise NodeNotInSelectionError()
        return node

    def add_node(self, node: bw_node.Node):
        self._node_list[node.identifier] = node

    def contains(self, node: bw_node.Node) -> bool:
        try:
            node = self._node_list[node.identifier]
        except KeyError:
            return False
        else:
            return True


@dataclass
class NodeChain(NodeGroupInterface):
    root: bw_node.Node

    def __post_init__(self):
        self.add_node(self.root)
    
    def add_node(self, node: bw_node.Node):
        super().add_node(node)
        node.chain = self

    def __str__(self) -> str:
        ret = f'NodeChain(root={self.root.label.encode()}' \
            f':{self.root.identifier}, children=(['
        for node in self.nodes[1:]:
            ret += f'{node.label.encode()}:{node.identifier}, '
        ret += '])'
        return ret


@dataclass()
class NodeSelection(NodeGroupInterface):
    """
    This class provides more detailed information about the selected API nodes.

    A hiararchy tree structure is built for the selection and nodes are
    categorized. The selection is then further broken down into a series of
    NodeChain objects.

    Nodes are converted into bw_node.Node objects
    """
    api_nodes: List[SDNode] = field(repr=False)
    api_graph: SDSBSCompGraph = field(repr=False)

    node_chains: List[NodeChain] = field(init=False,
                                         default_factory=list,
                                         repr=False)
    dot_nodes: List[bw_node.Node] = field(init=False,
                                          default_factory=list,
                                          repr=False)
    root_nodes: List[bw_node.Node] = field(init=False,
                                           default_factory=list,
                                           repr=False)

    def __post_init__(self):
        self._create_nodes()
        self._build_node_tree()
        self._sort_nodes()
        self._build_node_chains()

    @property
    def node_chain_count(self) -> int:
        return len(self.node_chains)

    # TODO: Move this into plugin and inherit
    def remove_dot_nodes(self) -> bool:
        """
        Removes all dot nodes in the selection
        """
        for dot_node in self.dot_nodes:
            dot_node = dot_node.api_node
            # Get property the connection comes from
            dot_node_input_property = dot_node.getPropertyFromId(
                'input', sd.api.sdproperty.SDPropertyCategory.Input
            )
            dot_node_input_connection = dot_node.getPropertyConnections(
                dot_node_input_property)[0]

            output_node_property = dot_node_input_connection.getInputProperty()
            output_node = dot_node_input_connection.getInputPropertyNode()

            # Get property the connection goes too
            dot_node_output_property = dot_node.getPropertyFromId(
                'unique_filter_output',
                sd.api.sdproperty.SDPropertyCategory.Output
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
                    input_node_property.getId()
                )

            self.api_graph.deleteNode(dot_node)
        return True

    def _build_node_chains(self):
        for root_node in self.root_nodes:
            self._build_new_node_chain(root_node)

    def _build_new_node_chain(self, root_node: bw_node.Node):
        # for output_node in root_node.output_nodes:
        #     output_node.remove_node_from_input_connection_data(root_node)

        # root_node.clear_output_connection_data()

        chain = NodeChain(root_node)
        self.node_chains.append(chain)
        self._add_children_to_node_chain(root_node, chain)

    def _add_children_to_node_chain(self,
                                    node: bw_node.Node,
                                    chain: NodeChain):
        for input_node in node.input_nodes:
            if input_node in self.root_nodes:
                continue

            chain.add_node(input_node)
            self._add_children_to_node_chain(input_node, chain)

    def _sort_nodes(self):
        for node in self.nodes:
            if node.is_root:
                self.root_nodes.append(node)

            if node.is_dot:
                self.dot_nodes.append(node)

    def _create_nodes(self):
        for api_node in self.api_nodes:
            node = bw_node.Node(api_node)
            self.add_node(node)

    def _build_node_tree(self):
        for identifier in self._node_list:
            node = self.node(identifier)
            self._add_input_nodes(node)
            self._add_output_nodes(node)

    def _add_input_nodes(self, node: bw_node.Node):
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
                connection = bw_node.InputConnectionData(index_in_node,
                                                         input_node)
                node.add_input_connection_data(connection)

    def _add_output_nodes(self, node: bw_node.Node):
        for index_in_node, api_property in enumerate(
            node.output_connectable_properties
        ):
            connection_data = bw_node.OutputConnectionData(index_in_node)

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
                node.add_output_connection_data(connection_data)
