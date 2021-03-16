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



class NodeSelection:
    def __init__(self, api_nodes: List[SDNode], api_graph: SDSBSCompGraph):
        self.api_graph = api_graph
        self.node = dict()
        self._parse_selection(api_nodes)

    @property
    def dot_nodes(self) -> Tuple[BWNode]:
        ret = []
        for node in self.node.values():
            if node.is_dot:
                ret.append(node)
        return tuple(ret)

    def contains(self, identifier: Union[str, int]) -> bool:
        try:
            node = self.node[int(identifier)]
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

    def _parse_selection(self, api_nodes) -> bool:
        for node in api_nodes:
            self.node[int(node.getIdentifier())] = bw_node.Node(node)
