from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

import sd
from bw_tools.common.bw_api_tool import (
    SDConnection,
    SDProperty,
    SDSBSCompGraph,
)
from bw_tools.common.bw_node import Node

STRIDE = 21.33  # Magic number between each input slot


@dataclass
class StraightenNode(Node):
    graph: SDSBSCompGraph = field(repr=False)

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
        self, dot_node: StraightenNode, input_node_property: SDProperty
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
    ) -> List[SDConnection]:
        p = self.api_node.getPropertyFromId(
            api_property_id, sd.api.sdproperty.SDPropertyCategory.Output
        )
        return [con for con in self.api_node.getPropertyConnections(p)]

    def _get_connected_output_connections_for_property(
        self, api_property: SDProperty
    ) -> List[SDConnection]:
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

    def get_position_of_output_index(self, i: int) -> float:
        lower_bound = self.pos.y
        for j in range(self.output_connectable_properties_count):
            lower_bound = max(self.pos.y + (STRIDE * j), lower_bound)
        mid_point = (self.pos.y + lower_bound) / 2
        offset = self.pos.y - mid_point
        return self.pos.y + offset + (STRIDE * i)
