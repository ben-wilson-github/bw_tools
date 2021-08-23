from __future__ import annotations
from bw_tools.common.bw_api_tool import SDSBSCompGraph

from dataclasses import dataclass, field
from bw_tools.common.bw_node import Node, SDProperty, SDConnection
from typing import TYPE_CHECKING, TypeVar

import sd

if TYPE_CHECKING:
    from bw_tools.modules.bw_straighten_connection.straighten_behavior import (
        AbstractStraightenBehavior,
    )

# TODO: MOVE Type vars to api tool


@dataclass
class ConnectionData:
    input_node: "StraightenNode"
    input_node_property: None
    index: int
    output_node: "StraightenNode" = field(init=False)
    output_node_property: None = field(init=False)


@dataclass
class StraightenNode(Node):
    graph: SDSBSCompGraph

    def y_position_of_property(self, source_property) -> float:
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

    # def rebuildConnection(self, aSourceNode, aDotNode):
    #     sourceIndex = aSourceNode.getIndexesToParent(aDotNode)[0]

    #     for parent in aDotNode.parents:
    #         # For this parent, get all the indexes in it
    #         targetIndexes = aDotNode.getIndexesInParent(parent)
    #         # Then reconnect the original source, to the target
    #         for targetIndex in targetIndexes:
    #             aSourceNode.connectToNode(sourceIndex, parent, targetIndex)

    # def deleteNode(self, aChild, aNodeToDelete):
    #     self.nodeSelection.graph.deleteNode(aNodeToDelete.apiNode)
    #     # aChild._parents.remove(aNodeToDelete)
    #     aChild._parents = None # Reset the parents to force the api to recompute them

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

    def straighten_connection_for_property(
        self, api_property, behavior: AbstractStraightenBehavior
    ):
        output_connections = (
            self._get_connected_output_connections_for_property(api_property)
        )
        output_connections.sort(
            key=lambda con: con.getInputPropertyNode().getPosition().x
        )

        source_node = self
        first = True
        for i, output_connection in enumerate(output_connections):
            if first:
                dot_node, target_node = self._insert_dot_node(
                    source_node, output_connection
                )
                behavior.position_first_dot(dot_node, source_node, target_node, i)

            dot_node, target_node = self._insert_dot_node(
                source_node, output_connection
            )
        
            FIGURE OUT POSITON LOGIC FOR PINS.
            Need to return custom class from get connections because I need to stack the inputs and each connection might
            be from the same output index. needs to include SDConnection and index its from
            return

            # behavior.position_dot(dot_node, source_node, target_node)

    def _insert_dot_node(
        self, source_node: StraightenNode, connection: SDConnection
    ):
        target_node = StraightenNode(
            connection.getInputPropertyNode(), self.graph
        )
        dot_node = StraightenNode(
            self.graph.newNode("sbs::compositing::passthrough"), self.graph
        )

        self._connect_node(source_node, dot_node, connection)
        self._connect_node(dot_node, target_node, connection)

        return dot_node, target_node

    def _connect_node(
        self,
        source_node: StraightenNode,
        target_node: StraightenNode,
        connection: SDConnection,
    ):
        source_property = self._get_source_property_from_connection(
            source_node, connection
        )
        target_property = self._get_target_property_from_connection(
            target_node, connection
        )
        source_node.api_node.newPropertyConnection(
            source_property, target_node.api_node, target_property
        )

    def _get_target_property_from_connection(
        self, target_node: StraightenNode, connection: SDConnection
    ):
        if target_node.is_dot:
            return target_node.api_node.getPropertyFromId(
                "input", sd.api.sdproperty.SDPropertyCategory.Input
            )
        return connection.getInputProperty()

    def _get_source_property_from_connection(
        self, source_node: StraightenNode, connection: SDConnection
    ):
        if source_node.is_dot:
            return source_node.api_node.getPropertyFromId(
                "unique_filter_output",
                sd.api.sdproperty.SDPropertyCategory.Output,
            )
        return connection.getOutputProperty()

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
