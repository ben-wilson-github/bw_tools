import importlib
from dataclasses import dataclass
from dataclasses import field
from modules import bw_generate_slider_outputs
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

class NodeNotInSelectionError(KeyError):
    def __init__(self):
        super().__init__('Node not in selection')

@dataclass
class NodeChain:
    root: bw_node.Node
    nodes: List[bw_node.Node] = field(init=False, default_factory=list)
    
    def __post_init__(self):
        self.add_node(self.root)

    def add_node(self, node: bw_node.Node):
        if node not in self.nodes:
            self.nodes.append(node)
            node.node_chain = self
    
    def __str__(self) -> str:
        ret = f'NodeChain(root={self.root.label.encode()}:{self.root.identifier}, children=(['
        for node in self.nodes[1:]:
            ret += f'{node.label.encode()}:{node.identifier}, '
        ret += '])'
        return ret


@dataclass()
class NodeSelection:
    api_nodes: List[SDNode] = field(repr=False)
    api_graph: SDSBSCompGraph = field(repr=False)

    node_chains: List[NodeChain] = field(init=False, default_factory=list, repr=False)
    dot_nodes: List[bw_node.Node] = field(init=False, default_factory=list, repr=False)
    root_nodes: List[bw_node.Node] = field(init=False, default_factory=list, repr=False)

    # Node list is a dictionary of identifier keys with a bw_node.Node object as value
    _node_list: dict = field(init=False, default_factory=dict)

    def __post_init__(self):
        self._create_nodes()
        self._build_node_tree()
        self._sort_nodes()
        self._build_node_chains()

    @property
    def node_chain_count(self) -> int:
        return len(self.node_chains)

    @property
    def nodes(self) -> Tuple[bw_node.Node]:
        ret = []
        for node in self._node_list.values():
            ret.append(node)
        return tuple(ret)

    @property
    def node_count(self) -> int:
        return len(self.nodes)

    def node(self, identifier: Union[str, int]) -> bw_node.Node:
        try:
            node = self._node_list[int(identifier)]
        except KeyError:
            raise NodeNotInSelectionError()
        else:
            return node

    def remove_dot_nodes(self) -> bool:
        for dot_node in self.dot_nodes:
            dot_node = dot_node.api_node
            # Get property the connection comes from
            dot_node_input_property = dot_node.getPropertyFromId('input', sd.api.sdproperty.SDPropertyCategory.Input)
            dot_node_input_connection = dot_node.getPropertyConnections(dot_node_input_property)[0]
            output_node_property = dot_node_input_connection.getInputProperty()

            output_node = dot_node_input_connection.getInputPropertyNode()

            # Get property the connection goes too
            dot_node_output_property = dot_node.getPropertyFromId('unique_filter_output',
                                                                  sd.api.sdproperty.SDPropertyCategory.Output)

            dot_node_output_connections = dot_node.getPropertyConnections(dot_node_output_property)
            for connection in dot_node_output_connections:
                input_node_property = connection.getInputProperty()
                input_node = connection.getInputPropertyNode()

                output_node.newPropertyConnectionFromId(output_node_property.getId(), input_node,
                                                        input_node_property.getId())

            self.api_graph.deleteNode(dot_node)
        return True


    def _build_node_chains(self):
        for root_node in self.root_nodes:
            self._build_new_node_chain(root_node)
        
    def _build_new_node_chain(self, root_node: bw_node.Node):
        for output_node in root_node.output_nodes:
            output_node.remove_node_from_input_connection_data(root_node)
        
        root_node.clear_output_connection_data()

        chain = NodeChain(root_node)
        self.node_chains.append(chain)
        self._add_children_to_node_chain(root_node, chain)

    def _add_children_to_node_chain(self, node: bw_node.Node, chain: NodeChain):
        for input_node in node.input_nodes:
            if input_node in self.root_nodes:
                continue
            
            chain.add_node(input_node)
            self._add_children_to_node_chain(input_node, chain)

    def _sort_nodes(self):
        for node in self.nodes:
            if node.is_root or node.output_node_count >= 2:
               self.root_nodes.append(node)

            if node.is_dot:
                self.dot_nodes.append(node)



    def _create_nodes(self):
        for api_node in self.api_nodes:
            node = bw_node.Node(api_node)
            self._node_list[node.identifier] = node

    def _build_node_tree(self):
        for identifier in self._node_list:
            node = self.node(identifier)
            self._add_input_nodes(node)
            self._add_output_nodes(node)
    
    def _add_input_nodes(self, node: bw_node.Node):
        for index_in_node, api_property in enumerate(node.input_connectable_properties):
            api_connections = node.api_node.getPropertyConnections(api_property)
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
                connection = bw_node.InputConnectionData(index_in_node, input_node)
                node.add_input_connection_data(connection)
                
    def _add_output_nodes(self, node: bw_node.Node):
        for index_in_node, api_property in enumerate(node.output_connectable_properties):
            connection_data = bw_node.OutputConnectionData(index_in_node)

            api_connections = node.api_node.getPropertyConnections(api_property)
            for api_connection in api_connections:
                output_api_node = api_connection.getInputPropertyNode()
                connection_data.add_node(self.node(output_api_node.getIdentifier()))
            
            if connection_data.nodes:
                node.add_output_connection_data(connection_data)


    # @staticmethod
    # def _set_chain_depth_property(node: bw_node.Node, output_node: bw_node.Node):
    #     indices = node.indices_in_target(output_node)
    #     for index in indices:
    #         connection_data = output_node.input_connection_data[index]
    #         connection_data.chain_depth = node.largest_input_chain_depth + 1

    # @staticmethod
    # def _set_mainline_property(node):
    #     largest_chain_node = node.input_node_with_largest_chain_depth
    #     for input_node in node.input_nodes:
    #         if input_node is largest_chain_node:
    #             input_node.mainline = True
    #         else:
    #             input_node.mainline = False
    #
    #     if node.is_root:
    #         node.mainline_node = True

    # def _calculate_downstream_data(self, node: BWNode):
    #     for output_node in node.output_nodes:
    #         self._set_chain_depth_property(node, output_node)
    #         self._calculate_downstream_data(output_node)

        # self._set_mainline_property(node)
