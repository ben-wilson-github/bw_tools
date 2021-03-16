from dataclasses import dataclass
from typing import Tuple
from typing import TypeVar

SDNode = TypeVar('sd.api.sdnode.SDNode')
SDArray = TypeVar('')
SDSBSCompGraph = TypeVar('sd.api.sbs.sdsbscompgraph.SDSBSCompGraph')

import sd


@dataclass()
class NodeSelection:
    nodes: SDArray
    graph: SDSBSCompGraph

    @property
    def dot_nodes(self) -> Tuple[SDNode]:
        ret = []
        for node in self.nodes:
            if node.getDefinition().getId() == 'sbs::compositing::passthrough':
                ret.append(node)
        return tuple(ret)

    def remove_dot_nodes(self) -> bool:
        for dot_node in self.dot_nodes:
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

            self.graph.deleteNode(dot_node)
        return True
