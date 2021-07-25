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

    # Node list is a dictionary of identifier keys with a bw_node.Node object as value
    _node_list: dict = field(init=False, default_factory=dict)
    # Node map is the tree structure of the selection
    _node_map: dict = field(init=False, default_factory=dict, repr=False)
    _end_nodes: list = field(init=False, default_factory=list, repr=False)
    _dot_nodes: List[bw_node.Node] = field(init=False, default_factory=list, repr=False)
    _root_nodes: list = field(init=False, default_factory=list, repr=False)
    _output_branching_nodes: list = field(init=False, default_factory=list, repr=False)
    _input_branching_nodes: list = field(init=False, default_factory=list, repr=False)

    _api_root_nodes = []

    def __post_init__(self):
        self._create_nodes()
        self._build_node_tree_api()
        self._categorize_nodes2()

        # print(self._root_nodes)

        # self._categorize_nodes()
        # self._build_node_chains()


    def _categorize_nodes2(self):
        nodes_left = list(self._node_list.keys())
        while nodes_left:
            # Do not .pop() as we need the nodes_left variable still.
            # .pop() will clear the memory
            identifier: int = nodes_left[0]
            nodes_left.remove(identifier)

            if not self._is_root(identifier):
                nodes_left.append(identifier)
                continue
            else:
                self._parse_root_node(identifier, nodes_left)
        
    def _parse_root_node(self, identifier: int, nodes_left: List[int]):
        node: bw_node.Node = self.node(identifier)
        chain = NodeChain(node)
        
        self._root_nodes.append(node)

        inputs = self._parse_inputs(node, nodes_left, chain)
        self._remove_identifiers_from_list(inputs, nodes_left)

        # outputs = self._parse_outputs(node, nodes_left, chain)
    
    def _remove_identifiers_from_list(identifiers: List[int], nodes_left: List[int]):
        # remove the inputs from the list
        for identifier in identifiers:
            try:
                nodes_left.remove(identifier)
            except ValueError:
                continue

    def _parse_outputs(self, node: bw_node.Node, nodes_left: List[int], chain: NodeChain) -> List[int]:
        unique_outputs = []

        output_identifier: int
        # for index, output_identifier in self._node_map[node.identifier]['outputs'].items():


    def _parse_inputs(self, node: bw_node.Node, nodes_left: List[int], chain: NodeChain) -> List[int]:
        # Collect a list of the inputs found, so we can remove them after we are done
        unique_inputs = []

        input_identifier: int
        for index, input_identifier in self._node_map[node.identifier]['inputs'].items():
            if self._is_root(input_identifier):
                continue

            if input_identifier not in unique_inputs:
                unique_inputs.append(input_identifier)

            input_node: bw_node.Node = self.node(input_identifier)

            MAYBE WE CAN ADD OUTPUT NODES AT THIS POINT?!

            # Create new connection
            connection = bw_node.InputConnectionData(index, input_node)
            node.add_input_connection_data(connection)

            chain.add_node(input_node)
            
            unique_inputs += self._parse_inputs(input_node, nodes_left, chain)
        
        return unique_inputs

    def _is_root(self, identifier):
        unique_outputs = []
        outputs = self._node_map[identifier]['outputs']
        for index in self._node_map[identifier]['outputs']:
            for output_identifier in outputs[index]:
                if output_identifier not in unique_outputs:
                    unique_outputs.append(output_identifier)
        return len(unique_outputs) != 1

            


                
    
    @property
    def node_chain_count(self) -> int:
        return len(self.node_chains)

    @property
    def dot_nodes(self) -> Tuple[bw_node.Node]:
        return tuple(self._dot_nodes)

    @property
    def root_nodes(self) -> Tuple[bw_node.Node]:
        return tuple(self._root_nodes)

    @property
    def end_nodes(self) -> Tuple[bw_node.Node]:
        return tuple(self._end_nodes)

    @property
    def input_branching_nodes(self) -> Tuple[bw_node.Node]:
        return tuple(self._input_branching_nodes)

    @property
    def output_branching_nodes(self) -> Tuple[bw_node.Node]:
        return tuple(self._output_branching_nodes)

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

    def _create_nodes(self):
        for api_node in self.api_nodes:
            node = bw_node.Node(api_node)
            self._node_list[node.identifier] = node

    def _categorize_nodes(self):
        for node in self._node_list.values():
            if node.is_dot:
                self._dot_nodes.append(node)

            if node.is_root:
                self._root_nodes.append(node)

            if node.is_end:
                self._end_nodes.append(node)

            if node.has_branching_outputs:
                self._output_branching_nodes.append(node)

            if node.has_branching_inputs:
                self._input_branching_nodes.append(node)

    def _build_node_tree_api(self):
        """
        Builds a tree hiarachy dictionary containing the inputs and outputs of every node.
        Nodes are represented by their identifiers
        """
        for identifier in self._node_list:
            self._node_map[identifier] = dict()

            node = self.node(identifier)
            self._node_map[identifier]['outputs'] = self._get_output_node_map(node)
            self._node_map[identifier]['inputs'] = self._get_input_node_map(node)

    def _get_input_node_map(self, node: bw_node.Node) -> Dict:
        input_node_map = dict()

        # A node may input into the a this node more than once
        # However, we only want to add one instance of it, so track
        # if its been added or not
        for index_in_node, api_property in enumerate(node.input_connectable_properties):
            input_node_map[index_in_node] = None

            connection = node.api_node.getPropertyConnections(api_property)
            if len(connection) == 0:
                continue

            # Because we are only looking at input properties. We can be sure
            # there will only be one connection or none at all. No need
            # to loop through all connections as there is only 1.
            input_api_node = connection[0].getInputPropertyNode()
            identifier = input_api_node.getIdentifier()
            try:
                self.node(identifier)
            except NodeNotInSelectionError:
                continue
            else:
                input_node_map[index_in_node] = int(identifier)
        return input_node_map

    def _get_output_node_map(self, node: bw_node.Node) -> Dict:
        output_node_map = dict()
        for index_in_node, property in enumerate(node.output_connectable_properties):
            output_node_map[index_in_node] = list()
            
            # It is possible that a node may output from a single index 
            # into another node multiple times. However, we only want
            # to count the number of unique output nodes
            for connection in node.api_node.getPropertyConnections(property):
                output_api_node = connection.getInputPropertyNode()
                identifier = output_api_node.getIdentifier()

                try:
                    self.node(identifier)
                except NodeNotInSelectionError:
                    continue
                else:
                    output_node_map[index_in_node].append(int(identifier))
        return output_node_map

    # def _build_node_tree(self):
    #     for identifier in self._node_list:
    #         node = self.node(identifier)
    #         self._add_output_nodes(node)
    #         self._add_input_nodes(node)

    # def _add_input_nodes(self, node: bw_node.Node):
    #     # A node may input into the some output node more than once
    #     # However, we only want to add one instance of it, so track
    #     # if its been added or not
    #     already_added = []
    #     for index_in_node, api_property in enumerate(node.input_connectable_properties):
    #         connection_data = bw_node.NodeConnectionData(index_in_node)
    #         node.input_connection_data.append(connection_data)

    #         connection = node.api_node.getPropertyConnections(api_property)
    #         if len(connection) == 0:
    #             continue

    #         # Because we are only looking at input properties. We can be sure
    #         # there will only be one connection or none at all. No need
    #         # to loop through all connections as there is only 1.
    #         api_node = connection[0].getInputPropertyNode()
    #         try:
    #             input_node = self.node(api_node.getIdentifier())
    #         except NodeNotInSelectionError:
    #             pass
    #         else:
    #             connection_data.nodes = input_node
    #             # TODO: I think this can be removed, we dont use bw_hiarachy anymore
    #             # if input_node not in already_added:
    #             #     connection_data.height = input_node.height
    #             already_added.append(input_node)

    # def _add_output_nodes(self, node: bw_node.Node):
    #     for index_in_node, property in enumerate(node.output_connectable_properties):
    #         connection_data = bw_node.NodeConnectionData(index_in_node)
    #         node.output_connection_data.append(connection_data)

    #         connection_data.nodes = []
    #         for connection in node.api_node.getPropertyConnections(property):
    #             output_api_node = connection.getInputPropertyNode()
    #             identifier = output_api_node.getIdentifier()
    #             try:
    #                 output_node = self.node(identifier)
    #             except NodeNotInSelectionError:
    #                 pass
    #             else:
    #                 connection_data.nodes.append(output_node)

    # def _build_node_chains(self):
    #     seen = []
    #     for root_node in self.root_nodes:
    #         self._build_node_chain(root_node, seen)
            
    # def _build_node_chain(self, root_node: bw_node.Node, seen: List[bw_node.Node]):
    #     seen.append(root_node)
    #     chain = NodeChain(root_node)
    #     self.node_chains.append(chain)
    #     for input_node in root_node.input_nodes:
    #         if input_node.has_branching_outputs:
    #             if input_node in seen:
    #                 continue
    #             self._build_node_chain(input_node, seen)
    #         else:
    #             chain.add_node(input_node)
    #             seen.append(input_node)

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
