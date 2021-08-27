from __future__ import annotations
from bw_tools.modules.bw_straighten_connection.bw_straighten_connection import (
    StraightenConnectionData,
    StraightenSettings,
)

from dataclasses import dataclass, field
from typing import Union, List

import sd
from bw_tools.common.bw_api_tool import SDSBSCompGraph
from bw_tools.common.bw_node import Node

# TODO: MOVE Type vars to api tool
# TODO: Snap to grid in layout tools option


STRIDE = 21.33  # Magic number between each input slot


class NoInputs(Exception):
    pass


@dataclass
class StraightenNode(Node):
    graph: SDSBSCompGraph
    output_dot_node: "StraightenNode" = field(
        repr=False, init=False, default=None
    )

    def delete_output_dot_nodes(self):
        for prop in self.output_connectable_properties:
            for con in self.api_node.getPropertyConnections(prop):
                dot_node = StraightenNode(
                    con.getInputPropertyNode(), self.graph
                )
                if not dot_node.is_dot:
                    continue

                dot_node.delete_output_dot_nodes()
                self._rebuild_deleted_dot_connection(
                    dot_node, con.getOutputProperty()
                )
                self.graph.deleteNode(dot_node.api_node)

    def _rebuild_deleted_dot_connection(
        self, dot_node: StraightenNode, input_node_property
    ):
        output_node_connections = (
            dot_node._get_connected_output_connections_for_property_id(
                "unique_filter_output"
            )
        )

        for output_node_con in output_node_connections:
            # I find api naming convension backwards
            # For me, input refers to the source node, output is the
            # destination node.
            output_node_property = output_node_con.getInputProperty()
            output_node = output_node_con.getInputPropertyNode()

            self.api_node.newPropertyConnection(
                input_node_property,
                output_node,
                output_node_property,
            )

    def _get_connected_output_connections_for_property_id(
        self, api_property_id: str
    ):
        p = self.api_node.getPropertyFromId(
            api_property_id, sd.api.sdproperty.SDPropertyCategory.Output
        )
        return [con for con in self.api_node.getPropertyConnections(p)]

    def _get_connected_output_connections_for_property(self, api_property):
        return [
            con for con in self.api_node.getPropertyConnections(api_property)
        ]

    def indices_in_target_node(self, target_node: StraightenNode) -> List[int]:
        return [
            i
            for i, p in enumerate(target_node.input_connectable_properties)
            for connection in target_node.api_node.getPropertyConnections(p)
            if connection.getInputPropertyNode().getIdentifier()
            == str(self.identifier)
        ]

    @property
    def center_index(self) -> Union[int, float]:
        if self.input_connectable_properties_count == 0:
            raise NoInputs()
        elif self.input_connectable_properties_count == 1:
            return 0
        elif self.input_connectable_properties_count == 2:
            return 0.5
        else:
            return 0.5 * (self.input_connectable_properties_count - 1)

    def output_nodes_in_front(
        self,
        settings: StraightenSettings,
    ):
        return [
            StraightenNode(con.getInputPropertyNode(), self.graph)
            for p in self.output_connectable_properties
            for con in self._get_connected_output_connections_for_property(p)
            if con
            and con.getInputPropertyNode().getPosition().x
            >= self.pos.x + settings.dot_node_distance * 2
        ]

    def conntects_to_center_index_of_target(self, target_node: StraightenNode):
        return target_node.center_index in self.indices_in_target_node(
            target_node
        )
    