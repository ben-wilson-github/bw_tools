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
# TODO: Snap to grid in layout tools option


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
        self,
        api_property: SDProperty,
        index: int,
        behavior: AbstractStraightenBehavior,
    ):
        return
        # # Insert target dot node
        # dot_node = self._insert_dot_node(
        #     source_node, target_node, output_connections[0]
        # )
        # behavior.position_dot(dot_node, source_node, target_node, index)
        # source_node = dot_node

        # # Insert remaining dot nodes
        # for output_connection in output_connections[1:]:
        #     new_target_node = StraightenNode(
        #         output_connection.getInputPropertyNode(), self.graph
        #     )
        #     if new_target_node.identifier == target_node.identifier:
        #         self._connect_node(dot_node, target_node, output_connection)
        #     else:
        #         dot_node = self._insert_dot_node(source_node, new_target_node, output_connection)
        #         behavior.position_dot(dot_node, source_node, new_target_node, index)
        #         source_node = dot_node


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
