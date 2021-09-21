from dataclasses import dataclass, field
from typing import List, Optional, Tuple

from bw_tools.common.bw_api_tool import CompNodeID, FunctionNodeId
from sd.api import sdbasetypes
from sd.api.sdconnection import SDConnection
from sd.api.sdgraphobjectcomment import SDGraphObjectComment
from sd.api.sdnode import SDNode
from sd.api.sdproperty import SDProperty, SDPropertyCategory


@dataclass
class BWFloat2:
    x: float = 0.0
    y: float = 0.0


@dataclass
class BWConnectionData:
    index: int


@dataclass
class BWInputConnectionData(BWConnectionData):
    input_node: "BWNode"


@dataclass
class BWOutputConnectionData(BWConnectionData):
    nodes: List["BWNode"] = field(init=False, default_factory=list)

    def add_node(self, node: "BWNode"):
        self.nodes.append(node)


@dataclass
class BWNode:
    api_node: SDNode = field(repr=False)

    label: str = field(init=False)
    identifier: int = field(init=False)
    pos: BWFloat2 = field(init=False, repr=False, default_factory=BWFloat2)

    _height: float = field(init=False, repr=False, default=-1)
    _input_connectable_properties: Optional[SDProperty] = field(
        init=False, repr=False, default=None
    )
    _output_connectable_properties: Optional[SDProperty] = field(
        init=False, repr=False, default=None
    )
    _input_nodes: Optional[Tuple["BWNode"]] = field(
        init=False, repr=False, default=None
    )
    _output_nodes: Optional[Tuple["BWNode"]] = field(
        init=False, repr=False, default=None
    )
    _input_connection_data: List[BWInputConnectionData] = field(
        init=False, default_factory=list, repr=False
    )
    _output_connection_data: List[BWOutputConnectionData] = field(
        init=False, default_factory=list, repr=False
    )

    def __post_init__(self):
        self.label = self.api_node.getDefinition().getLabel()
        self.identifier = int(self.api_node.getIdentifier())
        self.pos = BWFloat2(
            self.api_node.getPosition().x, self.api_node.getPosition().y
        )

    @property
    def height(self) -> float:
        if self._height != -1:
            return self._height

        connections = max(
            self.input_connectable_properties_count,
            self.output_connectable_properties_count,
        )
        if connections < 4:
            self._height = 96.0
            return self._height
        else:
            # adding a slot added 10.7 to a side
            delta = connections - 3
            self._height = 96.0 + ((10.7 * delta) * 2)
            return self._height

    @property
    def width(self) -> float:
        return 96.0

    @property
    def output_nodes(self) -> Tuple["BWNode"]:
        if self._output_nodes:
            return self._output_nodes

        unique_nodes = list()
        for connection in self._output_connection_data:
            for node in connection.nodes:
                if node not in unique_nodes:
                    unique_nodes.append(node)
        self._output_nodes = tuple(unique_nodes)
        return self._output_nodes

    @property
    def output_node_count(self) -> int:
        return len(self.output_nodes)

    @property
    def input_nodes(self) -> Tuple["BWNode"]:
        if self._input_nodes:
            return self._input_nodes

        unique_nodes = list()
        connection_data: BWInputConnectionData
        for connection_data in self._input_connection_data:
            input_node = connection_data.input_node

            if input_node not in unique_nodes:
                unique_nodes.append(input_node)
        self._input_nodes = tuple(unique_nodes)
        return self._input_nodes

    @property
    def input_node_count(self) -> int:
        return len(self.input_nodes)

    @property
    def has_input_nodes_connected(self) -> bool:
        return self.input_node_count > 0

    @property
    def input_connectable_properties(self) -> Tuple[SDProperty]:
        """Returns all API properties which are connectable for all inputs"""
        if self._input_connectable_properties:
            return self._input_connectable_properties

        self._input_connectable_properties = (
            self._connectable_properties_from_category(
                SDPropertyCategory.Input
            )
        )
        return self._input_connectable_properties

    @property
    def output_connectable_properties(self) -> Tuple[SDProperty]:
        """Returns all API properties which are connectable for all outputs"""
        if self._output_connectable_properties:
            return self._output_connectable_properties

        self._output_connectable_properties = (
            self._connectable_properties_from_category(
                SDPropertyCategory.Output
            )
        )
        return self._output_connectable_properties

    @property
    def input_connectable_properties_count(self) -> int:
        return len(self.input_connectable_properties)

    @property
    def output_connectable_properties_count(self) -> int:
        return len(self.output_connectable_properties)

    @property
    def output_connections(self) -> Tuple[SDConnection]:
        connections = list()
        for property in self.output_connectable_properties:
            for connection in self.api_node.getPropertyConnections(property):
                connections.append(connection)
        return tuple(connections)

    @property
    def is_dot(self) -> bool:
        return (
            self.api_node.getDefinition().getId() == CompNodeID.DOT.value
            or self.api_node.getDefinition().getId()
            == FunctionNodeId.DOT.value
        )

    @property
    def is_root(self) -> bool:
        return self.output_node_count == 0

    @property
    def has_branching_outputs(self) -> bool:
        return self.output_node_count > 1

    @property
    def has_branching_inputs(self) -> bool:
        return self.input_node_count > 1

    def add_input_connection_data(self, data: BWConnectionData):
        self._input_connection_data.append(data)

    def add_output_connection_data(self, data: BWConnectionData):
        self._output_connection_data.append(data)

    def set_position(self, x, y):
        self.pos.x = x
        self.pos.y = y
        self.api_node.setPosition(sdbasetypes.float2(x, y))

    def add_comment(self, msg: str):
        comment: SDGraphObjectComment = SDGraphObjectComment.sNewAsChild(
            self.api_node
        )
        comment.setPosition(sdbasetypes.float2(64, 0))
        comment.setDescription(msg)

    def _connectable_properties_from_category(
        self, category
    ) -> Tuple[SDProperty]:
        connectable_properties = []
        for p in self.api_node.getProperties(category):
            if p.isConnectable():
                connectable_properties.append(p)
        return tuple(connectable_properties)
