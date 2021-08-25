from __future__ import annotations
from dataclasses import dataclass, field
from bw_tools.common.bw_node import Float2, SDConnection, SDProperty
from bw_tools.modules.bw_straighten_connection.straighten_behavior import (
    NextToOutput,
)

from functools import partial
from pathlib import Path
from typing import TYPE_CHECKING, List, Tuple, TypeVar, Dict

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

DISTANCE = 96


@dataclass
class BaseDotNodeBounds:
    upper_bound: int = 0
    lower_bound: int = 0


@dataclass
class StraightenConnectionData:
    connection: Dict[int, SDConnection] = field(default_factory=dict)
    base_dot_node: Dict[int, StraightenNode] = field(default_factory=dict)
    current_source_node: Dict[int, StraightenNode] = field(
        default_factory=dict
    )
    stack_index: Dict[int, int] = field(default_factory=dict)
    properties_with_outputs_count: int = 0
    base_dot_nodes_bounds: BaseDotNodeBounds = field(
        default_factory=BaseDotNodeBounds
    )


def run_straighten_connection(
    source_node: StraightenNode,
    behavior: AbstractStraightenBehavior,
    api: APITool,
):
    data = _create_connection_data_for_all_inputs(source_node)
    _create_base_dot_nodes(source_node, data, behavior)
    behavior.align_base_dot_nodes(source_node, data)

    _insert_target_dot_nodes(source_node, data, behavior)

    if (
        behavior.delete_base_dot_nodes
        and source_node.output_connectable_properties_count
        == data.properties_with_outputs_count
    ):
        _delete_base_dot_nodes(source_node, data)


def _create_connection_data_for_all_inputs(
    source_node: StraightenNode,
) -> StraightenConnectionData:
    data = StraightenConnectionData()
    for i, api_property in enumerate(
        source_node.output_connectable_properties
    ):
        cons = source_node._get_connected_output_connections_for_property(
            api_property
        )
        cons.sort(key=lambda c: c.getInputPropertyNode().getPosition().x)
        data.connection[i] = cons
        if cons:
            data.properties_with_outputs_count += 1
    return data


def _create_base_dot_nodes(
    source_node: StraightenNode,
    data: StraightenConnectionData,
    behavior: AbstractStraightenBehavior,
):
    """
    Creates dot nodes at the base of the source node. The dot nodes
    are stacked downwards from the source nodes position.y.

    These dot nodes will either be connected or deleted later, depending
    on if the the resulting connections line up with the output pins
    of the node.

    Returns the upper and lower bound of the new dot nodes
    """
    # Store initial bound values
    upper_y = source_node.pos.y
    lower_y = source_node.pos.y
    index = 0
    for i, _ in enumerate(source_node.output_connectable_properties):
        if not data.connection[i]:
            continue
        connection = data.connection[i][0]

        # Stack the node
        # Create base dot node
        dot_node = StraightenNode(
            source_node.graph.newNode("sbs::compositing::passthrough"),
            source_node.graph,
        )
        data.base_dot_node[i] = dot_node
        data.current_source_node[i] = source_node

        if (
            source_node.output_connectable_properties_count
            != data.properties_with_outputs_count
        ):
            _connect_node(source_node, dot_node, connection)
            data.current_source_node[i] = dot_node

        first_target_node = StraightenNode(
            connection.getInputPropertyNode(), source_node.graph
        )
        pos = behavior.get_position_first_dot(
            source_node.pos, first_target_node.pos, index
        )
        dot_node.set_position(pos.x, pos.y)

        upper_y = min(pos.y, upper_y)  # Designer Y axis is inverted
        lower_y = max(pos.y, lower_y)
        data.stack_index[i] = index
        index += 1

    data.base_dot_nodes_bounds.upper_bound = upper_y
    data.base_dot_nodes_bounds.lower_bound = lower_y


def _should_reconnect_with_previous(
    previous: StraightenNode,
    next: StraightenNode,
    data: StraightenConnectionData,
    i: int,
):
    return (
        previous.identifier == next.identifier
        or data.base_dot_node[i].pos.y == next.pos.y
        or next.pos.x - DISTANCE <= previous.pos.x
    )


def _insert_target_dot_nodes(
    source_node: StraightenNode,
    data: StraightenConnectionData,
    behavior: AbstractStraightenBehavior,
):
    for i, _ in enumerate(source_node.output_connectable_properties):
        if not data.connection[i]:
            continue

        previous_target_node = None
        for connection in data.connection[i]:
            next_target_node = StraightenNode(
                connection.getInputPropertyNode(), source_node.graph
            )
            target_dot_pos: Float2 = behavior.get_position_target_dot(
                data.base_dot_node[i].pos,
                next_target_node.pos,
                data.stack_index[i],
            )

            if previous_target_node is not None and _should_reconnect_with_previous(
                previous_target_node, next_target_node, data, i
            ):
                _connect_node(
                    data.current_source_node[i], next_target_node, connection
                )
            else:
                # Create target dot node
                new_dot_node = StraightenNode(
                    source_node.graph.newNode("sbs::compositing::passthrough"),
                    source_node.graph,
                )
                new_dot_node.set_position(target_dot_pos.x, target_dot_pos.y)
                _connect_node(
                    data.current_source_node[i], new_dot_node, connection
                )
                _connect_node(new_dot_node, next_target_node, connection)
                data.current_source_node[i] = new_dot_node
                previous_target_node = next_target_node


def _delete_base_dot_nodes(
    source_node: StraightenNode, data: StraightenConnectionData
):
    for i, _ in enumerate(source_node.output_connectable_properties):
        if not data.connection[i]:
            continue
        source_node.graph.deleteNode(data.base_dot_node[i].api_node)


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
