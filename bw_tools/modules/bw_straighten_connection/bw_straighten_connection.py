from __future__ import annotations
from bw_tools.modules.bw_straighten_connection.straighten_behavior import (
    NextToOutput
)

from functools import partial
from pathlib import Path
from typing import TYPE_CHECKING, List, Tuple, TypeVar

# import sd
from PySide2 import QtGui
from sd.api.sdhistoryutils import SDHistoryUtils

from .straighten_node import StraightenNode

if TYPE_CHECKING:
    from bw_tools.common.bw_api_tool import APITool
    from bw_tools.modules.bw_straighten_connection.straighten_behavior import AbstractStraightenBehavior


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
    node: StraightenNode, behavior, api: APITool
):
    for index, api_property in enumerate(node.output_connectable_properties):
        node.straighten_connection_for_property(api_property, behavior)


def on_clicked_straighten_connection(api: APITool):
    with SDHistoryUtils.UndoGroup("Straighten Connection Undo Group"):
        api.logger.info("Running straighten connection")

        for node in api.current_selection:
            node = StraightenNode(node)
            node.delete_output_dot_nodes(api.current_graph)
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
