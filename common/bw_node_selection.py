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

    def __post_init__(self):
        self._create_nodes()
        self._build_node_tree()

    @property
    def dot_nodes(self) -> Tuple[BWNode]:
        ret = []
        for node in self._node_map.values():
            if node.is_dot:
                ret.append(node)
        return tuple(ret)

    @property
    def root_nodes(self) -> Tuple[BWNode]:
        ret = []
        for node in self._node_map.values():
            if node.is_root():
                ret.append(node)
        return tuple(ret)

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

    def _build_node_tree(self):
        for identifier in self._node_map:
            self._add_output_nodes(self._node_map[identifier])
            self._add_input_nodes(self._node_map[identifier])

    def _add_input_nodes(self, node: bw_node.Node):
        for i, p in enumerate(node.input_connectable_properties):
            # Because we are only looking at input properties. We can be sure
            # there will only be one connection or none at all
            connection = node.api_node.getPropertyConnections(p)
            if len(connection) == 0:
                node._input_nodes[i] = None
            else:
                api_node = connection[0].getInputPropertyNode()
                node._input_nodes[i] = self.node(api_node.getIdentifier())

    def _add_output_nodes(self, node: bw_node.Node):
        for i, p in enumerate(node.output_connectable_properties):
            node._output_nodes[i] = []
            for connection in node.api_node.getPropertyConnections(p):
                api_node = connection.getInputPropertyNode()
                identifier = api_node.getIdentifier()
                node_in_selection = self.node(identifier)
                if node_in_selection is not None:
                    node._output_nodes[i].append(node_in_selection)
