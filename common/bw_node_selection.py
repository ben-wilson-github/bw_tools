import importlib
from dataclasses import dataclass
from dataclasses import field
from typing import List
from typing import Dict
from typing import Union
from typing import Tuple
from typing import TypeVar

from common import bw_node
importlib.reload(bw_node)

import sd
SDNode = TypeVar('sd.api.sdnode.SDNode')
SDArray = TypeVar('sd.api.sdarray.SDArray')
SDSBSCompGraph = TypeVar('sd.api.sbs.sdsbscompgraph.SDSBSCompGraph')
BWNode = TypeVar('bw_node.Node')


@dataclass()
class NodeSelection:
    api_nodes: List[SDNode] = field(repr=False)
    api_graph: SDSBSCompGraph = field(repr=False)
    _node_map: dict = field(init=False, default_factory=dict)
    _end_nodes: list = field(init=False, default_factory=list)
    _root_nodes: list = field(init=False, default_factory=list)
    _dot_nodes: list = field(init=False, default_factory=list)

    def __post_init__(self):
        self._create_nodes()
        self._build_node_tree()
        self._categorize_nodes()
        for node in self.end_nodes:
            self._count_nodes(node)

    @property
    def dot_nodes(self) -> Tuple[BWNode]:
        return tuple(self._dot_nodes)

    @property
    def root_nodes(self) -> Tuple[BWNode]:
        return tuple(self._root_nodes)

    @property
    def end_nodes(self) -> Tuple[BWNode]:
        return tuple(self._end_nodes)

    @property
    def nodes(self) -> Tuple[BWNode]:
        ret = []
        for node in self._node_map.values():
            ret.append(node)
        return tuple(ret)

    @property
    def node_count(self) -> int:
        return len(self.nodes)

    def node(self, identifier: Union[str, int]) -> Union[BWNode, None]:
        try:
            node = self._node_map[int(identifier)]
        except KeyError:
            return None
        else:
            return node

    def contains(self, identifier: Union[str, int]) -> bool:
        try:
            node = self._node_map[int(identifier)]
        except KeyError:
            return False
        else:
            return True

    def remove_dot_nodes(self) -> bool:
        for dot_node in self.dot_nodes:
            dot_node = dot_node.api_node
            # Get property the connection comes from
            dot_node_input_property = dot_node.getPropertyFromId('input', sd.api.sdproperty.SDPropertyCategory.Input)
            dot_node_input_connection = dot_node.getPropertyConnections(dot_node_input_property)[0]
            output_node_property = dot_node_input_connection.getInputProperty()

            output_node = dot_node_input_connection.getInputPropertyNode()

            # Get property the connection goes too
            dot_node_output_property = dot_node.getPropertyFromId('unique_filter_output', sd.api.sdproperty.SDPropertyCategory.Output)

            dot_node_output_connections = dot_node.getPropertyConnections(dot_node_output_property)
            for connection in dot_node_output_connections:
                input_node_property = connection.getInputProperty()
                input_node = connection.getInputPropertyNode()

                output_node.newPropertyConnectionFromId(output_node_property.getId(), input_node, input_node_property.getId())

            self.api_graph.deleteNode(dot_node)
        return True

    def _create_nodes(self):
        for node in self.api_nodes:
            self._node_map[int(node.getIdentifier())] = bw_node.Node(node)

    def _categorize_nodes(self):
        for node in self._node_map.values():
            if node.is_dot:
                self._dot_nodes.append(node)

            if node.is_root:
                self._root_nodes.append(node)

            if node.is_end:
                self._end_nodes.append(node)

    def _build_node_tree(self):
        for identifier in self._node_map:
            self._add_output_nodes(self._node_map[identifier])
            self._add_input_nodes(self._node_map[identifier])

    def _add_input_nodes(self, node: bw_node.Node):
        seen = []
        for i, p in enumerate(node.input_connectable_properties):
            connection_data = bw_node.NodeConnectionData(i)
            node.input_connection_data.append(connection_data)

            connection = node.api_node.getPropertyConnections(p)
            if len(connection) == 0:
                continue

            # Because we are only looking at input properties. We can be sure
            # there will only be one connection or none at all
            api_node = connection[0].getInputPropertyNode()
            if self.contains(api_node.getIdentifier()):
                node_in_selection = self.node(api_node.getIdentifier())
                connection_data.nodes = node_in_selection
                if node_in_selection not in seen:
                    connection_data.height = node_in_selection.height
                seen.append(node_in_selection)

    def _add_output_nodes(self, node: bw_node.Node):
        for i, p in enumerate(node.output_connectable_properties):
            connection_data = bw_node.NodeConnectionData(i)
            node.output_connection_data.append(connection_data)
            connection_data.nodes = []
            for connection in node.api_node.getPropertyConnections(p):
                api_node = connection.getInputPropertyNode()
                identifier = api_node.getIdentifier()
                node_in_selection = self.node(identifier)
                if node_in_selection is not None:
                    connection_data.nodes.append(node_in_selection)

    def _count_nodes(self, node: BWNode):
        if node.is_root:
            return

        for output_node in node.output_nodes:
            indices = node.indices_in_target(output_node)
            for index in indices:
                connection_data = output_node.input_connection_data[index]
                connection_data.chain_depth = node.largest_input_chain_depth + 1

            self._count_nodes(output_node)
