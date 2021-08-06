from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, List, Tuple, TypeVar

import sd

if TYPE_CHECKING:
    from bw_tools.common import bw_node_selection

SDSBSCompNode = TypeVar("SDSBSCompNode")
SDProperty = TypeVar("SDProperty")
SDSBSCompGraph = TypeVar("SDSBSCompGraph")

# TODO: Move this to settings
SPACER = 32
# Pixel values about the UI
NODE_BOADER_WIDTH = 26.75
NODE_SLOT_STRIDE = 21.25


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
        connections = max(
            self.input_connectable_properties_count,
            self.output_connectable_properties_count,
        )
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
    def output_nodes(self) -> Tuple["Node"]:
        unique_nodes = list()
        for connection in self._output_connection_data:
            for node in connection.nodes:
                if node not in unique_nodes:
                    unique_nodes.append(node)
        return tuple(unique_nodes)

    @property
    def output_node_count(self) -> int:
        return len(self.output_nodes)

    @property
    def input_nodes(self) -> Tuple["Node"]:
        unique_nodes = list()

        connection_data: InputConnectionData
        for connection_data in self._input_connection_data:
            input_node = connection_data.input_node

            if input_node not in unique_nodes:
                unique_nodes.append(input_node)
        return tuple(unique_nodes)

    @property
    def input_node_count(self) -> int:
        return len(self.input_nodes)

    @property
    def has_input_nodes_connected(self) -> bool:
        return self.input_node_count > 0

    @property
    def input_connectable_properties(self) -> Tuple[SDProperty]:
        """Returns all API properties which are connectable for all inputs"""
        return self._connectable_properties_from_category(
            sd.api.sdproperty.SDPropertyCategory.Input
        )

    @property
    def output_connectable_properties(self) -> Tuple[SDProperty]:
        """Returns all API properties which are connectable for all outputs"""
        return self._connectable_properties_from_category(
            sd.api.sdproperty.SDPropertyCategory.Output
        )

    @property
    def input_connectable_properties_count(self) -> int:
        return len(self.input_connectable_properties)

    @property
    def output_connectable_properties_count(self) -> int:
        return len(self.output_connectable_properties)

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

    def y_position_of_property(self, source_property: SDProperty) -> float:
        if (
            source_property.getCategory()
            == sd.api.sdproperty.SDPropertyCategory.Input
        ):
            relevant_properties = self.input_connectable_properties
        elif (
            source_property.getCategory()
            == sd.api.sdproperty.SDPropertyCategory.Output
        ):
            relevant_properties = self.output_connectable_properties
        else:
            raise ValueError(
                f"Unable to get height of property {source_property}. It must "
                "be an Input or Output category property."
            )

        index = None
        for i, p in enumerate(relevant_properties):
            if source_property.getId() == p.getId():
                index = i
                break
        if index is None:
            raise ValueError(
                f"Unable to get height of property {source_property}. "
                "It does not belong to this node."
            )

        if len(relevant_properties) < 2:
            return self.pos.y
        elif len(relevant_properties) == 2:
            if index == 0:
                offset = -10.75
            else:
                offset = 10.75
            return self.pos.y + offset
        else:
            inner_area = (
                (len(relevant_properties) - 1) * self.display_slot_stride
            ) / 2
            return (self.pos.y - inner_area) + self.display_slot_stride * index

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
