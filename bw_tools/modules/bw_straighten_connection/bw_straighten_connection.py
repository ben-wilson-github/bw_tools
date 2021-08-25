from __future__ import annotations
from dataclasses import dataclass, field
from bw_tools.common.bw_node import Float2, SDConnection
from bw_tools.modules.bw_settings.bw_settings import ModuleSettings
from .straighten_behavior import (
    BreakAtSource,
    BreakAtTarget,
)

from functools import partial
from pathlib import Path
from typing import TYPE_CHECKING, Dict

import sd
from PySide2 import QtGui
from sd.api.sdhistoryutils import SDHistoryUtils

from .straighten_node import StraightenNode

if TYPE_CHECKING:
    from bw_tools.common.bw_api_tool import APITool
    from .straighten_behavior import (
        AbstractStraightenBehavior,
    )


# # TODO: Check if can remove the list copy in remove dot nodes

STRIDE = 21.33  # Magic number between each input slot


class StraightenSettings(ModuleSettings):
    def __init__(self, file_path: Path):
        super().__init__(file_path)
        self.hotkey: str = self.get("Hotkey;value")
        self.remove_dot_nodes_hotkey: str = self.get(
            "Remove Connected Dot Nodes Hotkey;value"
        )
        self.dot_node_distance: str = self.get("Dot Node Distance;value")
        self.alignment_behavior: str = self.get("Alignment Behavior;value")


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
    settings: StraightenSettings,
):
    data = _create_connection_data_for_all_inputs(source_node)
    _create_base_dot_nodes(source_node, data, behavior, settings)
    behavior.align_base_dot_nodes(source_node, data)

    _insert_target_dot_nodes(source_node, data, behavior, settings)

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
    settings: StraightenSettings,
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

        if behavior.connect_base_dot_nodes(source_node, data):
            _connect_node(source_node, dot_node, connection)
            data.current_source_node[i] = dot_node

        pos = Float2(
            source_node.pos.x + settings.dot_node_distance,
            source_node.pos.y + (STRIDE * index),
        )
        dot_node.set_position(pos.x, pos.y)

        upper_y = min(pos.y, upper_y)  # Designer Y axis is inverted
        lower_y = max(pos.y, lower_y)
        data.stack_index[i] = index
        index += 1

    data.base_dot_nodes_bounds.upper_bound = upper_y
    data.base_dot_nodes_bounds.lower_bound = lower_y


def _insert_target_dot_nodes(
    source_node: StraightenNode,
    data: StraightenConnectionData,
    behavior: AbstractStraightenBehavior,
    settings: StraightenSettings
):
    for i, _ in enumerate(source_node.output_connectable_properties):
        if not data.connection[i]:
            continue

        previous_target_node = source_node
        for connection in data.connection[i]:
            next_target_node = StraightenNode(
                connection.getInputPropertyNode(), source_node.graph
            )
            target_dot_pos: Float2 = behavior.get_position_target_dot(
                data.base_dot_node[i].pos,
                next_target_node.pos,
                data.stack_index[i],
                settings
            )

            if behavior.reuse_previous_dot_node(
                previous_target_node, next_target_node, data, i, settings
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

        settings = StraightenSettings(
            Path(__file__).parent / "bw_straighten_connection_settings.json"
        )
        for node in api.current_selection:
            node = StraightenNode(node, api.current_graph)
            node.delete_output_dot_nodes()

            if settings.alignment_behavior == 0:
                behavior = BreakAtSource(api.current_graph)
            else:
                behavior = BreakAtTarget(api.current_graph)

            run_straighten_connection(node, behavior, settings)


def on_clicked_remove_dot_nodes_from_selection(api: APITool):
    with SDHistoryUtils.UndoGroup("Remove Dot Nodes Undo Group"):
        api.logger.info("Running remove dot nodes from selection")

        for node in api.current_selection:
            try:
                node = StraightenNode(node, api.current_graph)
            except AttributeError:
                continue

            node.delete_output_dot_nodes()


TARGET NODE IS BEING PLACED BEHIND THE ROOT ON SOURCE BEHAVIOR

def on_graph_view_created(_, api: APITool):
    settings = StraightenSettings(
        Path(__file__).parent / "bw_straighten_connection_settings.json"
    )
    print(settings)

    icon = Path(__file__).parent / "resources" / "straighten_connection.png"
    action = api.graph_view_toolbar.addAction(
        QtGui.QIcon(str(icon.resolve())), ""
    )
    action.setShortcut(QtGui.QKeySequence(settings.hotkey))
    action.setToolTip("Straighten connections on selected nodes.")
    action.triggered.connect(lambda: on_clicked_straighten_connection(api))

    icon = Path(__file__).parent / "resources" / "remove_dot_node_selected.png"
    action = api.graph_view_toolbar.addAction(
        QtGui.QIcon(str(icon.resolve())), ""
    )
    action.setShortcut(QtGui.QKeySequence(settings.remove_dot_nodes_hotkey))
    action.setToolTip("Remove dot nodes from selected nodes.")
    action.triggered.connect(
        lambda: on_clicked_remove_dot_nodes_from_selection(api)
    )


def on_initialize(api: APITool):
    api.register_on_graph_view_created_callback(
        partial(on_graph_view_created, api=api)
    )
