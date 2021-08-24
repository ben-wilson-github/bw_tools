from __future__ import annotations
from bw_tools.common.bw_node import Float2, SDConnection, SDProperty
from bw_tools.modules.bw_straighten_connection.straighten_behavior import (
    NextToOutput,
)

from functools import partial
from pathlib import Path
from typing import TYPE_CHECKING, List, Tuple, TypeVar

import sd
from PySide2 import QtGui
from sd.api.sdhistoryutils import SDHistoryUtils

from .straighten_node import StraightenNode

if TYPE_CHECKING:
    from bw_tools.common.bw_api_tool import APITool
    from bw_tools.modules.bw_straighten_connection.straighten_behavior import (
        AbstractStraightenBehavior,
    )


# # TODO: Check if can remove the list copy in remove dot nodes


# # def node_is_too_close(
# #     source_node: sd.api.sdnode.SDNode,
# #     target_node: sd.api.sdnode.SDNode,
# #     threshold: float,
# # ) -> bool:
# #     if source_node.getPosition().x < target_node.getPosition().x - threshold:
# #         return False
# #     else:
# #         return True


# # def sort_connections_by_position_x(
# #     connections: sd.api.sdconnection.SDConnection,
# # ) -> Tuple[sd.api.sdconnection.SDConnection]:
# #     sorted_list = list(connections)
# #     swapped = True
# #     while swapped:
# #         swapped = False
# #         for i in range(len(sorted_list) - 1):
# #             if (
# #                 sorted_list[i].getInputPropertyNode().getPosition().x
# #                 == sorted_list[i + 1].getInputPropertyNode().getPosition().x
# #             ):
# #                 if (
# #                     sorted_list[i].getInputPropertyNode().getPosition().y
# #                     == sorted_list[i + 1]
# #                     .getInputPropertyNode()
# #                     .getPosition()
# #                     .y
# #                 ):
# #                     if (
# #                         sorted_list[i].getInputPropertyNode().getIdentifier()
# #                         > sorted_list[i + 1]
# #                         .getInputPropertyNode()
# #                         .getIdentifier()
# #                     ):
# #                         sorted_list[i], sorted_list[i + 1] = (
# #                             sorted_list[i + 1],
# #                             sorted_list[i],
# #                         )
# #                         swapped = True

# #                 elif (
# #                     sorted_list[i].getInputPropertyNode().getPosition().y
# #                     > sorted_list[i + 1].getInputPropertyNode().getPosition().y
# #                 ):
# #                     sorted_list[i], sorted_list[i + 1] = (
# #                         sorted_list[i + 1],
# #                         sorted_list[i],
# #                     )
# #                     swapped = True
# #             elif (
# #                 sorted_list[i].getInputPropertyNode().getPosition().x
# #                 > sorted_list[i + 1].getInputPropertyNode().getPosition().x
# #             ):
# #                 sorted_list[i], sorted_list[i + 1] = (
# #                     sorted_list[i + 1],
# #                     sorted_list[i],
# #                 )
# #                 swapped = True
# #     return tuple(sorted_list)


# # def insert_dot_node(
# #     graph: sd.api.sbs.sdsbscompgraph.SDSBSCompGraph,
# #     source_node: sd.api.sdnode.SDNode,
# #     source_property: sd.api.sdproperty.SDProperty,
# #     target_node: sd.api.sdnode.SDNode,
# #     target_property: sd.api.sdproperty.SDProperty,
# #     threshold: float,
# # ) -> sd.api.sdnode.SDNode:
# #     dot_node = graph.newNode("sbs::compositing::passthrough")

# #     source_node.newPropertyConnection(
# #         source_property,
# #         dot_node,
# #         dot_node.getPropertyFromId(
# #             "input", sd.api.sdproperty.SDPropertyCategory.Input
# #         ),
# #     )

# #     dot_node.newPropertyConnection(
# #         dot_node.getPropertyFromId(
# #             "unique_filter_output", sd.api.sdproperty.SDPropertyCategory.Output
# #         ),
# #         target_node,
# #         target_property,
# #     )

# #     # position_at_source = get_from_settings_file(
# #     #     __file__.replace(".py", "_settings.json"), "Position At Source"
# #     # )
# #     # if position_at_source:
# #     #     x = bw_node.Node(source_node).pos.x + threshold
# #     #     y = bw_node.Node(target_node).y_position_of_property(target_property)
# #     # else:
# #     x = StraightenNode(target_node).pos.x - threshold
# #     y = StraightenNode(source_node).y_position_of_property(source_property)

# #     dot_node.setPosition(sd.api.sdbasetypes.float2(x, y))
# #     return dot_node


# # def is_dot_node(node: SDNode) -> bool:
# #     return node.getDefinition().getId() == "sbs::compositing::passthrough"


# # def get_connections_for_node_property(
# #     graph: SDSBSCompGraph,
# #     source_node: SDNode,
# #     source_node_property: SDProperty,
# # ) -> List[SDConnection]:
# #     def already_seen(src, ret):
# #         for c in ret:
# #             if (
# #                 c.getInputPropertyNode().getIdentifier()
# #                 == src.getInputPropertyNode().getIdentifier()
# #                 and c.getInputProperty().getId()
# #                 == src.getInputProperty().getId()
# #             ):
# #                 return True
# #         return False

# #     ret = list()
# #     for connection in source_node.getPropertyConnections(source_node_property):
# #         next_node_in_chain = connection.getInputPropertyNode()
# #         if is_dot_node(next_node_in_chain):
# #             ret += get_connections_for_node_property(
# #                 graph,
# #                 next_node_in_chain,
# #                 next_node_in_chain.getPropertyFromId(
# #                     "unique_filter_output",
# #                     sd.api.sdproperty.SDPropertyCategory.Output,
# #                 ),
# #             )
# #             graph.deleteNode(connection.getInputPropertyNode())
# #         else:
# #             if already_seen(connection, ret):
# #                 continue
# #             ret.append(connection)
# #     return ret


# # def straighten_connection(
# #     source_node: SDNode,
# #     source_node_property: SDProperty,
# #     api: APITool,
# # ):

# #     threshold = 96

# #     connections = get_connections_for_node_property(
# #         api.current_graph, source_node, source_node_property
# #     )
# #     sorted_connections = sort_connections_by_position_x(connections)

# #     dot_node = None
# #     for connection in sorted_connections:
# #         if dot_node is None:  # On first iteration
# #             if node_is_too_close(
# #                 source_node, connection.getInputPropertyNode(), threshold
# #             ):
# #                 continue
# #             else:
# #                 dot_node = insert_dot_node(
# #                     api.current_graph,
# #                     source_node,
# #                     source_node_property,
# #                     connection.getInputPropertyNode(),
# #                     connection.getInputProperty(),
# #                     threshold,
# #                 )
# #         else:
# #             if node_is_too_close(
# #                 dot_node,
# #                 connection.getInputPropertyNode(),
# #                 threshold + (threshold / 2),
# #             ):
# #                 dot_node.newPropertyConnection(
# #                     dot_node.getPropertyFromId(
# #                         "unique_filter_output",
# #                         sd.api.sdproperty.SDPropertyCategory.Output,
# #                     ),
# #                     connection.getInputPropertyNode(),
# #                     connection.getInputProperty(),
# #                 )
# #             else:
# #                 dot_node = insert_dot_node(
# #                     api.current_graph,
# #                     dot_node,
# #                     dot_node.getPropertyFromId(
# #                         "unique_filter_output",
# #                         sd.api.sdproperty.SDPropertyCategory.Output,
# #                     ),
# #                     connection.getInputPropertyNode(),
# #                     connection.getInputProperty(),
# #                     threshold,
# #                 )




def run_straighten_connection(
    source_node: StraightenNode,
    behavior: AbstractStraightenBehavior,
    api: APITool,
):
    # Insert first dot nodes
    upper_y = source_node.pos.y
    lower_y = source_node.pos.y
    connections: List[SDConnection] = list()
    base_dot_nodes: List[StraightenNode] = list()
    target_nodes: List[StraightenNode] = list()
    connection_data = dict()
    
    # Get connections
    property_with_target_count = 0
    for i, api_property in enumerate(source_node.output_connectable_properties):
        cons = (
            source_node._get_connected_output_connections_for_property(
                api_property
            )
        )
        cons.sort(
            key=lambda c: c.getInputPropertyNode().getPosition().x
        )
        connection_data[i] = {
            "connections": cons
        }
        if cons:
            property_with_target_count += 1
    

    # Create base dot nodes
    index = 0
    for i, _ in enumerate(source_node.output_connectable_properties):
        if not connection_data[i]["connections"]:
            continue
        connection = connection_data[i]["connections"][0]

        # Stack the node
        # Create base dot node
        dot_node = StraightenNode(
            source_node.graph.newNode("sbs::compositing::passthrough"),
            source_node.graph,
        )
        connection_data[i]['dot_node'] = dot_node
        connection_data[i]['source_node'] = source_node

        if source_node.output_connectable_properties_count != property_with_target_count:
            _connect_node(source_node, dot_node, connection)
            connection_data[i]['source_node'] = dot_node

        first_target_node = StraightenNode(
            connection.getInputPropertyNode(), source_node.graph
        )
        pos = behavior.get_position_first_dot(source_node.pos, first_target_node.pos, index)
        dot_node.set_position(pos.x, pos.y)
        upper_y = min(pos.y, upper_y)   # Designer Y axis is inverted
        lower_y = max(pos.y, lower_y)
        connection_data[i]["stack_index"] = index
        index += 1



    mid_point = (upper_y + lower_y) / 2
    offset = source_node.pos.y - mid_point
    # Position base dot nodes. Move to behavior
    for i, _ in enumerate(source_node.output_connectable_properties):
        if not connection_data[i]["connections"]:
            continue
        
        dot_node: StraightenNode = connection_data[i]["dot_node"]
        dot_node.set_position(dot_node.pos.x, dot_node.pos.y + offset)
        connection_data[i]["pos"] = dot_node.pos

    GOT LOGIC WORKING AGAIN. NEED TO ADD TARGET DOT NODE BEING REMOVED IF ITS INLINE
    THEN DO A BIG REFACTOR
    
    # Insert target dot nodes
    for i, _ in enumerate(source_node.output_connectable_properties):
        if not connection_data[i]["connections"]:
            continue

        previous_dot_node: StraightenNode = connection_data[i]['source_node']
        previous_target_node = None
        # Insert any remaining dot nodes
        for connection in connection_data[i]["connections"]:
            target_node = StraightenNode(
                connection.getInputPropertyNode(), source_node.graph
            )
            if previous_target_node is not None and previous_target_node.identifier == target_node.identifier:
                # reconnect with previous dot node
                _connect_node(previous_dot_node, target_node, connection)
            else:
                # Create target dot node
                new_dot_node = StraightenNode(
                    source_node.graph.newNode("sbs::compositing::passthrough"),
                    source_node.graph,
                )

                pos = behavior.get_position_dot(connection_data[i]["pos"], target_node.pos, connection_data[i]["stack_index"])
                new_dot_node.set_position(pos.x, pos.y)
                _connect_node(previous_dot_node, new_dot_node, connection)
                _connect_node(new_dot_node, target_node, connection)
                previous_dot_node = new_dot_node
                previous_target_node = target_node
    
    # remove floating dot nodes if any
    if source_node.output_connectable_properties_count == property_with_target_count:
        for i, _ in enumerate(source_node.output_connectable_properties):
            if not connection_data[i]["connections"]:
                continue
            source_node.graph.deleteNode(connection_data[i]['dot_node'].api_node)


def _connect_node(
    source_node: StraightenNode,
    target_node: StraightenNode,
    connection: SDConnection,
):
    source_property = _get_source_property_from_connection(
        source_node, connection
    )
    target_property = _get_target_property_from_connection(
        target_node, connection
    )
    source_node.api_node.newPropertyConnection(
        source_property, target_node.api_node, target_property
    )


def _get_target_property_from_connection(
    target_node: StraightenNode, connection: SDConnection
):
    if target_node.is_dot:
        return target_node.api_node.getPropertyFromId(
            "input", sd.api.sdproperty.SDPropertyCategory.Input
        )
    return connection.getInputProperty()


def _get_source_property_from_connection(
    source_node: StraightenNode, connection: SDConnection
):
    if source_node.is_dot:
        return source_node.api_node.getPropertyFromId(
            "unique_filter_output",
            sd.api.sdproperty.SDPropertyCategory.Output,
        )
    return connection.getOutputProperty()

    # Align them

    # node.straighten_connection_for_property(api_property, index, behavior)


def on_clicked_straighten_connection(api: APITool):
    with SDHistoryUtils.UndoGroup("Straighten Connection Undo Group"):
        api.logger.info("Running straighten connection")

        for node in api.current_selection:
            node = StraightenNode(node, api.current_graph)
            node.delete_output_dot_nodes()
            run_straighten_connection(
                node, NextToOutput(api.current_graph), api
            )


def on_graph_view_created(_, api: APITool):
    icon = Path(__file__).parent / "resources" / "straighten_connection.png"
    action = api.graph_view_toolbar.addAction(
        QtGui.QIcon(str(icon.resolve())), ""
    )
    action.setToolTip("Straighten connections on selected nodes.")
    action.triggered.connect(lambda: on_clicked_straighten_connection(api))

    icon = Path(__file__).parent / "resources" / "remove_dot_node_selected.png"
    action = api.graph_view_toolbar.addAction(
        QtGui.QIcon(str(icon.resolve())), ""
    )
    action.setToolTip("Remove dot nodes from selected nodes.")


def on_initialize(api: APITool):
    api.register_on_graph_view_created_callback(
        partial(on_graph_view_created, api=api)
    )
