from __future__ import annotations
from dataclasses import dataclass
from dataclasses import field
from typing import Union
from typing import Tuple
from typing import TypeVar
from typing import List

from common import bw_connection, bw_node_selection
from common import bw_utils
from common import bw_chain_dimension

import sd

SDSBSCompNode = TypeVar('SDSBSCompNode')
SDProperty = TypeVar('SDProperty')
SDConnection = TypeVar('SDConnection')
SDSBSCompGraph = TypeVar('SDSBSCompGraph')
SDNode = TypeVar('sd.api.sdnode.SDNode')
ChainDimension = TypeVar('bw_chain_dimension.ChainDimension')

# TODO: Move this to settings
SPACER = 32
# Pixel values about the UI
NODE_BOADER_WIDTH = 26.75
NODE_SLOT_STRIDE = 21.25

@dataclass()
class NodePosition:
    x: float
    y: float

    def __post_init__(self):
        if not any(isinstance(i, float) for i in [self.x, self.y]):
            raise TypeError(bw_utils.invalid_type_error(self.__init__, self.x, self.y))


@dataclass()
class ConnectionData:
    index: int
    # height: int = field(init=False, default=0)
    # chain_depth: int = field(init=False, default=0)
    # branches: List['Node'] = field(init=False, default_factory=list)

@dataclass
class InputConnectionData(ConnectionData):
    input_node: 'Node'

@dataclass
class OutputConnectionData(ConnectionData):
    nodes: List['Node'] = field(init=False, default_factory=list)

    def add_node(self, node: 'Node'):
        self.nodes.append(node)



@dataclass()
class Node:
    api_node: 'SDSBSCompNode' = field(repr=False)
    # node_selection: bw_node_selection = field(init=False, repr=False)
    node_chain: bw_node_selection.NodeChain = field(init=False, repr=False, compare=False)

    label: str = field(init=False)
    identifier: int = field(init=False)
    pos: NodePosition = field(init=False, repr=False)

    _input_connection_data: List[InputConnectionData] = field(init=False, default_factory=list, repr=False)
    _output_connection_data: List[OutputConnectionData] = field(init=False, default_factory=list, repr=False)

    closest_output_node: 'Node' = field(init=False, default=None, repr=None)
    mainline: bool = field(init=False, default=False, repr=False)
    chain_dimension: ChainDimension = field(init=False, default=None, repr=False)
    # _output_nodes: dict = field(init=False, default_factory=dict, repr=False)
    # _input_nodes: dict = field(init=False, default_factory=dict, repr=False)
    # _input_node_heights: dict = field(init=False, default_factory=dict, repr=False)

    def __post_init__(self):
        # if not isinstance(self.api_node, sd.api.sbs.sdsbscompnode.SDSBSCompNode):
        #     raise TypeError(bw_utils.invalid_type_error(self.__init__, self.api_node))
        self.label = self.api_node.getDefinition().getLabel()
        self.identifier = int(self.api_node.getIdentifier())
        self.pos = NodePosition(self.api_node.getPosition().x, self.api_node.getPosition().y)

    def add_input_connection_data(self, data: ConnectionData):
        self._input_connection_data.append(data)

    def add_output_connection_data(self, data: ConnectionData):
        self._output_connection_data.append(data)

    @property
    def has_label(self) -> bool:
        if not self.label:
            return False
        else:
            return True

    @property
    def height(self) -> float:
        connections = max(self.input_connectable_properties_count, self.output_connectable_properties_count)
        if connections < 4:
            return 96.0
        else:
            # adding a slot added 10.7 to a side
            delta = connections - 3
            return 96.0 + ((10.7 * delta) * 2)

    @property
    def width(self) -> float:
        return 96.0

    @property
    def referenced_graph_identifier(self) -> Union[int, None]:
        rsc = self.api_node.getReferencedResource()
        if rsc is None:
            return None
        else:
            return int(rsc.getIdentifier())

    @property
    def input_connectable_properties_count(self) -> int:
        return len(self.input_connectable_properties)

    @property
    def output_connectable_properties_count(self) -> int:
        return len(self.output_connectable_properties)

    @property
    def input_connectable_properties(self) -> Tuple[SDProperty]:
        """Returns all API properties which are connectable for all inputs"""
        return self._connectable_properties_from_category(sd.api.sdproperty.SDPropertyCategory.Input)

    @property
    def output_connectable_properties(self) -> Tuple[SDProperty]:
        """Returns all API properties which are connectable for all outputs"""
        return self._connectable_properties_from_category(sd.api.sdproperty.SDPropertyCategory.Output)

    @property
    def is_dot(self) -> bool:
        return self.api_node.getDefinition().getId() == 'sbs::compositing::passthrough'

    @property
    def is_root(self) -> bool:
        """
        If a node does not have any outputs, it is considered a root node.
        An optional node selection can be passed in to limit the output node checks to only
        those in the selection.
        """
        return self.output_node_count == 0

    @property
    def is_end(self) -> bool:
        return self.input_node_count == 0

    @property
    def has_branching_outputs(self) -> bool:
        return self.output_node_count > 1

    @property
    def has_branching_inputs(self) -> bool:
        return self.input_node_count > 1

    @property
    def output_node_count(self) -> int:
        return len(self.output_nodes)

    @property
    def output_nodes(self) -> Tuple['Node']:
        unique_nodes = list()
        for connection in self._output_connection_data:
            for node in connection.nodes:
                if node not in unique_nodes:
                    unique_nodes.append(node)
        return tuple(unique_nodes)


    @property
    def input_node_count(self) -> int:
        return len(self.input_nodes)

    @property
    def input_nodes(self) -> Tuple['Node', ...]:
        unique_nodes = []

        connection_data: InputConnectionData
        for connection_data in self._input_connection_data:
            if connection_data.input_node not in unique_nodes:
                unique_nodes.append(connection_data.input_node)
        return tuple(unique_nodes)

    @property
    def has_input_nodes_connected(self):
        return self.input_node_count > 0

    @property
    def center_input_index(self) -> float:
        return (self.input_connectable_properties_count - 1) / 2

    @property
    def input_nodes_height_sum(self) -> float:
        sum = 0
        for connection_data in self._input_connection_data:
            sum += connection_data.height
        return sum

    @property
    def largest_input_chain_depth(self) -> int:
        return self._calculate_largest_chain_depth()[0]

    @property
    def input_node_with_largest_chain_depth(self) -> 'Node':
        index = self.largest_chain_depth_index
        return self.input_node_in_index(index)

    @property
    def input_chains_are_equal_depth(self) -> bool:
        largest = self.largest_input_chain_depth
        for cd in self._input_connection_data:
            if cd.chain_depth == 0:
                continue
            if cd.chain_depth != largest:
                return False
        return True

    @property
    def largest_chain_depth_index(self) -> int:
        return self._calculate_largest_chain_depth()[1]
    
    def clear_input_connection_data(self):
        self._input_connection_data = list()
    
    def clear_output_connection_data(self):
        self._output_connection_data = list()
    
    def remove_node_from_input_connection_data(self, node: 'Node'):
        for connection in self._input_connection_data:
            if node == connection.input_node:
                self._input_connection_data.remove(connection)

    def is_largest_chain_in_target(self, target_node: 'Node') -> bool:
        index = self.indices_in_target(target_node)[0] # Assume top index
        return index == target_node.largest_chain_depth_index

    def input_node_height_in_index(self, index) -> float:
        connection_data = self._input_connection_data[index]
        return connection_data.height

    def connects_above_largest_chain_in_target(self, target_node: Node) -> bool:
        return self.indices_in_target(target_node)[0] < target_node.largest_chain_depth_index

    def connects_below_largest_chain_in_target(self, target_node: Node) -> bool:
        return self.indices_in_target(target_node)[0] > target_node.largest_chain_depth_index

    def connects_above_center(self, target_node: Node) -> bool:
        return any(i < target_node.center_input_index for i in self.indices_in_target(target_node))

    def connects_below_center(self, target_node: Node) -> bool:
        return any(i > target_node.center_input_index for i in self.indices_in_target(target_node))

    def connects_to_center(self, target_node: Node) -> bool:
        return target_node.center_input_index in self.indices_in_target(target_node)

    def indices_in_target(self, target_node: Node) -> List[int]:
        """Returns all the indices that this node connects to in target node"""
        indices = []
        for connection_data in target_node._input_connection_data:
            if connection_data.nodes is self:
                indices.append(connection_data.index)
        return indices

    def set_position(self, x, y):
        self.pos.x = x
        self.pos.y = y
        self.api_node.setPosition(
            sd.api.sdbasetypes.float2(x, y)
        )
    
    def move_to_node(self, other: Node, offset_x: float = 0, offset_y: float = 0):
        """Helper function to position a node to another"""
        self.set_position(other.pos.x + offset_x, other.pos.y + offset_y)

    def output_node_count_in_index(self, index) -> int:
        return len(self.output_nodes_in_index(index))

    def output_nodes_in_index(self, index) -> Tuple['Node']:
        ret = []
        for connection_data in self._output_connection_data:
            if connection_data.index != index:
                continue

            for node in connection_data.nodes:
                if node not in ret:
                    ret.append(node)
        return tuple(ret)

    def input_node_in_index(self, index) -> Union['Node', None]:
        for connection_data in self._input_connection_data:
            if connection_data.index != index:
                continue
            else:
                return connection_data.nodes
        return None

    def is_connected_to_node(self, target_node: 'Node') -> bool:
        if not isinstance(target_node, Node):
            raise TypeError(bw_utils.invalid_type_error(
                self.is_connected_to_node, target_node)
            )

        for p in self.output_connectable_properties:
            for node in self.input_nodes_connected_to_property(p):
                if node.identifier == target_node.identifier:
                    return True
        return False

    def y_position_of_property(self, source_property: SDProperty) -> float:
        if source_property.getCategory() == sd.api.sdproperty.SDPropertyCategory.Input:
            relevant_properties = self.input_connectable_properties
        elif source_property.getCategory() == sd.api.sdproperty.SDPropertyCategory.Output:
            relevant_properties = self.output_connectable_properties
        else:
            raise ValueError(
                f'Unable to get height of property {source_property}. It must be an Input or Output category property.')

        index = None
        for i, p in enumerate(relevant_properties):
            if source_property.getId() == p.getId():
                index = i
                break
        if index is None:
            raise ValueError(f'Unable to get height of property {source_property}. It does not belong to this node.')

        if len(relevant_properties) < 2:
            return self.pos.y
        elif len(relevant_properties) == 2:
            if index == 0:
                offset = -10.75
            else:
                offset = 10.75
            return self.pos.y + offset
        else:
            inner_area = ((len(relevant_properties) - 1) * self.display_slot_stride) / 2
            return (self.pos.y - inner_area) + self.display_slot_stride * index

    def add_comment(self, msg: str):
        comment = sd.api.sdgraphobjectcomment.SDGraphObjectComment.sNewAsChild(self.api_node)
        comment.setPosition(sd.api.sdbasetypes.float2(64, 0))
        comment.setDescription(msg)

    def _connectable_properties_from_category(self, category) -> Tuple[SDProperty]:
        connectable_properties = []
        for p in self.api_node.getProperties(category):
            if p.isConnectable():
                connectable_properties.append(p)
        return tuple(connectable_properties)

    def _calculate_largest_chain_depth(self) -> Tuple[int, int]:
        largest = 0
        index = 0
        for cd in self._input_connection_data:
            if cd.chain_depth > largest:
                largest = cd.chain_depth
                index = cd.index
        return largest, index

    # ====================================================
    # To refactor
    # ====================================================
    # @property
    # def inputs_connected_count(self) -> int:
    #     count = 0
    #     for i in range(self.input_slot_count):
    #         if self.input_has_connection(i):
    #             count += 1
    #     return count
    #
    # @property
    # def outputs_connected_count(self) -> int:
    #     count = 0
    #     for i in range(self.output_slot_count):
    #         if self.output_has_connection(i):
    #             count += 1
    #     return count
    #
    # def get_input_connections(self):
    #     if not any(self.input_has_connection(i) for i in range(self.input_slot_count)):
    #         return tuple()
    #     ret = []
    #     for i in range(self.input_slot_count):
    #         try:
    #             con = self.get_input(i)
    #         except AttributeError:
    #             continue
    #         else:
    #             ret.append(con)
    #
    #     return tuple(ret)
    #
    # def get_outputs_connections(self):
    #     if not any(self.output_has_connection(i) for i in range(self.output_slot_count)):
    #         raise AttributeError('Unable to get outputs, Node has no outputs')
    #     ret = []
    #     for i in range(self.output_slot_count):
    #         try:
    #             con = self.get_output(i)
    #         except AttributeError:
    #             continue
    #         else:
    #             ret.append(con)
    #
    #     return tuple(ret)
    #
    # def get_input(self, index):
    #     p = self.get_property_from_input_slot(index)
    #     nodes = self.get_api_nodes_connected_to_property(p)
    #     if len(nodes) == 0:
    #         raise AttributeError(f'Unable to get input in slot {index}. Slot has no inputs')
    #     else:
    #         return bw_connection.InputConnection(int(nodes[0].getIdentifier()))
    #
    # def get_output(self, index):
    #     p = self.get_property_from_output_slot(index)
    #     nodes = self.get_api_nodes_connected_to_property(p)
    #     if len(nodes) == 0:
    #         raise AttributeError(f'Unable to get outputs in slot {index}. Slot has no outputs')
    #     else:
    #         ids = [int(n.getIdentifier()) for n in nodes]
    #         return bw_connection.OutputConnection(ids)
    #
    # def input_has_connection(self, index):
    #     try:
    #         self.get_input(index)
    #     except AttributeError:
    #         return False
    #     else:
    #         return True
    #
    # def output_has_connection(self, index):
    #     try:
    #         self.get_output(index)
    #     except AttributeError:
    #         return False
    #     else:
    #         return True
    #
    # def get_property_from_input_slot(self, index):
    #     for i, p in enumerate(self.input_connectable_properties):
    #         if i == index:
    #             return p
    #     return None
    #
    # def get_property_from_output_slot(self, index):
    #     for i, p in enumerate(self.output_connectable_properties):
    #         if i == index:
    #             return p
    #     raise IndexError(f'Unable to get property from output slot {index}. Index is out of reach.')
    #
    # def get_api_nodes_connected_to_property(self, prop):
    #     connected_nodes = []
    #     connections = self.api_node.getPropertyConnections(prop)
    #     for connected_wire in connections:
    #         input_node = connected_wire.getInputPropertyNode()
    #         connected_nodes.append(input_node)
    #     return tuple(connected_nodes)
