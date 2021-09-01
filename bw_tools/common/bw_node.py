from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional, List, Tuple, TypeVar

import sd

SDSBSCompNode = TypeVar("SDSBSCompNode")
SDProperty = TypeVar("SDProperty")
SDSBSCompGraph = TypeVar("SDSBSCompGraph")
SDConnection = TypeVar("SDConnection")


@dataclass
class Float2:
    x: float = 0.0
    y: float = 0.0


@dataclass
class ConnectionData:
    index: int


@dataclass
class InputConnectionData(ConnectionData):
    input_node: "Node"


@dataclass
class OutputConnectionData(ConnectionData):
    nodes: List["Node"] = field(init=False, default_factory=list)

    def add_node(self, node: "Node"):
        self.nodes.append(node)


@dataclass
class Node:
    api_node: "SDSBSCompNode" = field(repr=False)

    label: str = field(init=False)
    identifier: int = field(init=False)
    pos: Float2 = field(init=False, repr=False, default_factory=Float2)

    _height: float = field(init=False, repr=False, default=-1)
    _input_connectable_properties: Optional[SDProperty] = field(
        init=False, repr=False, default=None
    )
    _output_connectable_properties: Optional[SDProperty] = field(
        init=False, repr=False, default=None
    )
    _input_nodes: Optional[Tuple["Node"]] = field(
        init=False, repr=False, default=None
    )
    _output_nodes: Optional[Tuple["Node"]] = field(
        init=False, repr=False, default=None
    )
    _input_connection_data: List[InputConnectionData] = field(
        init=False, default_factory=list, repr=False
    )
    _output_connection_data: List[OutputConnectionData] = field(
        init=False, default_factory=list, repr=False
    )

    def __post_init__(self):
        self.label = self.api_node.getDefinition().getLabel()
        self.identifier = int(self.api_node.getIdentifier())
        self.pos = Float2(
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
    def output_nodes(self) -> Tuple["Node"]:
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
    def input_nodes(self) -> Tuple["Node"]:
        if self._input_nodes:
            return self._input_nodes

        unique_nodes = list()
        connection_data: InputConnectionData
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
                sd.api.sdproperty.SDPropertyCategory.Input
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
                sd.api.sdproperty.SDPropertyCategory.Output
            )
        )
        return self._output_connectable_properties

    @property
    def input_connectable_properties_count(self) -> int:
        return len(self.input_connectable_properties)

    @property
    def output_connectable_properties_count(self) -> int:
        return len(self.output_connectable_properties)

    # TODO Move to straighten connection module and use enum
    @property
    def is_dot(self) -> bool:
        return (
            self.api_node.getDefinition().getId()
            == "sbs::compositing::passthrough"
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

    def add_input_connection_data(self, data: ConnectionData):
        self._input_connection_data.append(data)

    def add_output_connection_data(self, data: ConnectionData):
        self._output_connection_data.append(data)

    def set_position(self, x, y):
        self.pos.x = x
        self.pos.y = y
        self.api_node.setPosition(sd.api.sdbasetypes.float2(x, y))

    def add_comment(self, msg: str):
        comment = sd.api.sdgraphobjectcomment.SDGraphObjectComment.sNewAsChild(
            self.api_node
        )
        comment.setPosition(sd.api.sdbasetypes.float2(64, 0))
        comment.setDescription(msg)

    def _connectable_properties_from_category(
        self, category
    ) -> Tuple[SDProperty]:
        connectable_properties = []
        for p in self.api_node.getProperties(category):
            if p.isConnectable():
                connectable_properties.append(p)
        return tuple(connectable_properties)
