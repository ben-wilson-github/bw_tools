import sd
from dataclasses import dataclass
from dataclasses import field
from typing import Union
from typing import Tuple
from typing import TypeVar
from typing import List

from common import bw_connection
from common import bw_utils

SDSBSCompNode = TypeVar('SDSBSCompNode')
SDProperty = TypeVar('SDProperty')
SDConnection = TypeVar('SDConnection')
SDSBSCompGraph = TypeVar('SDSBSCompGraph')


@dataclass()
class NodePosition:
    x: float
    y: float

    def __post_init__(self):
        if not any(isinstance(i, float) for i in [self.x, self.y]):
            raise TypeError(bw_utils.type_error_message(self.__init__, self.x, self.y))


@dataclass()
class Node:
    api_node: 'SDSBSCompNode'
    label: str = field(init=False)
    identifier: int = field(init=False)
    position: NodePosition = field(init=False)
    display_border: float = field(init=False, default=26.75)
    display_slot_stride: float = field(init=False, default=21.25)

    def __post_init__(self):
        if not isinstance(self.api_node, sd.api.sbs.sdsbscompnode.SDSBSCompNode):
            raise TypeError(bw_utils.type_error_message(self.__init__, self.api_node))
        self.label = self.api_node.getDefinition().getLabel()
        self.identifier = int(self.api_node.getIdentifier())
        self.position = NodePosition(self.api_node.getPosition().x, self.api_node.getPosition().y)

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
        return self._get_connectable_properties_from_category(sd.api.sdproperty.SDPropertyCategory.Input)

    @property
    def output_connectable_properties(self) -> Tuple[SDProperty]:
        return self._get_connectable_properties_from_category(sd.api.sdproperty.SDPropertyCategory.Output)

    @property
    def is_dot(self):
        return self.api_node.getDefinition().getId() == 'sbs::compositing::passthrough'

    def get_output_nodes(self, node_selection=None) -> Tuple[Node]:
        """
        Returns the connected output nodes.
        If a node selection is passed in, will return only the output nodes in
        that selection.
        """
        seen = []
        ret = []
        for p in self.output_connectable_properties:
            for connection in self.api_node.getPropertyConnections(p):
                identifier = connection.getInputPropertyNode().getIdentifier()
                if identifier in seen:
                    continue
                seen.append(identifier)
                if node_selection is not None and not node_selection.contains(identifier):
                    continue
                ret.append(Node(connection.getInputPropertyNode()))
        return tuple(ret)

    def get_output_nodes_count(self, node_selection=None) -> int:
        """
        Returns the connected output nodes.
        If a node selection is passed in, will return only the the output nodes
        count in that selection
        """
        return len(self.get_output_nodes(node_selection))


    def get_property_connections_input_nodes(self, p: SDProperty) -> Tuple['Node']:
        if not isinstance(p, sd.api.sdproperty.SDProperty):
            raise TypeError(bw_utils.type_error_message(
                self.get_property_connections_input_nodes, p)
            )

        ret = list()
        for connection in self.api_node.getPropertyConnections(p):
            node = Node(connection.getInputPropertyNode())
            ret.append(node)
        return tuple(ret)

    def get_property_connections_input_nodes_count(self, p: SDProperty) -> int:
        if not isinstance(p, sd.api.sdproperty.SDProperty):
            raise TypeError(bw_utils.type_error_message(
                self.get_property_connections_input_nodes_count, p)
            )

        return len(self.get_property_connections_input_nodes(p))

    def get_property_connections(self, p: SDProperty) -> List[SDConnection]:
        if not isinstance(p, sd.api.sdproperty.SDProperty):
            raise TypeError(bw_utils.type_error_message(
                self.get_property_connections, p)
            )

        return self.api_node.getPropertyConnections(p)

    def get_property_connections_count(self, p: SDProperty) -> int:
        if not isinstance(p, sd.api.sdproperty.SDProperty):
            raise TypeError(bw_utils.type_error_message(
                self.get_property_connections_count, p)
            )
        return len(self.get_property_connections(p))

    def is_connected_to_node(self, target_node: 'Node') -> bool:
        if not isinstance(target_node, Node):
            raise TypeError(bw_utils.type_error_message(
                self.is_connected_to_node, target_node)
            )

        for p in self.output_connectable_properties:
            for node in self.get_property_connections_input_nodes(p):
                if node.identifier == target_node.identifier:
                    return True
        return False

    def get_y_position_of_property(self, source_property: SDProperty) -> float:
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
            return self.position.y
        elif len(relevant_properties) == 2:
            if index == 0:
                offset = -10.75
            else:
                offset = 10.75
            return self.position.y + offset
        else:
            inner_area = ((len(relevant_properties) - 1) * self.display_slot_stride) / 2
            return (self.position.y - inner_area) + self.display_slot_stride * index

    def _get_connectable_properties_from_category(self, category) -> Tuple[SDProperty]:
        connectable_properties = []
        for p in self.api_node.getProperties(category):
            if p.isConnectable():
                connectable_properties.append(p)
        return tuple(connectable_properties)

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
