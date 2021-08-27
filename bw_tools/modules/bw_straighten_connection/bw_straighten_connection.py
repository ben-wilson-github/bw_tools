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
from typing import TYPE_CHECKING, Dict, List

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
    connection: Dict[int, List[SDConnection]] = field(default_factory=dict)
    base_dot_node: Dict[int, StraightenNode] = field(default_factory=dict)
    # stack_index: Dict[int, int] = field(default_factory=dict)
    properties_with_outputs_count: int = 0
    # base_dot_nodes_bounds: BaseDotNodeBounds = field(
    #     default_factory=BaseDotNodeBounds
    # )
    output_nodes: Dict[int, List[StraightenNode]] = field(default_factory=dict)


def run_straighten_connection(
    source_node: StraightenNode,
    behavior: AbstractStraightenBehavior,
    settings: StraightenSettings,
):
    data = _create_connection_data_for_all_inputs(source_node)
    _create_base_dot_nodes(source_node, data, behavior, settings)
    _align_base_dot_nodes(source_node, data, behavior, settings)
    _insert_target_dot_nodes(source_node, data, behavior, settings)
    # _delete_base_dot_nodes(source_node, data, behavior, settings)


def _delete_base_dot_nodes(
    source_node: StraightenNode,
    data: StraightenConnectionData,
    behavior: AbstractStraightenBehavior,
    settings: StraightenSettings,
):
    for i in range(source_node.output_connectable_properties_count):
        if data.base_dot_node[i] is None:
            continue

        if behavior.should_delete_base_dot_node(
            source_node, data, i, settings
        ):
            dot_node = data.base_dot_node[i]
            _connect_node(
                source_node, dot_node.output_dot_node, data.connection[i][0]
            )
            source_node.graph.deleteNode(data.base_dot_node[i].api_node)


def _align_base_dot_nodes(
    source_node: StraightenNode,
    data: StraightenConnectionData,
    behavior: AbstractStraightenBehavior,
    settings: StraightenSettings,
):
    for i, _ in enumerate(source_node.output_connectable_properties):
        if data.base_dot_node[i] is None:
            continue
        behavior.align_base_dot_node(source_node, data, i, settings)


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
        data.output_nodes[i] = [
            StraightenNode(con.getInputPropertyNode(), source_node.graph)
            for con in cons
        ]
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
    # Store initial bound values
    stack_index = 0
    for i, _ in enumerate(source_node.output_connectable_properties):
        data.base_dot_node[i] = None
        # data.stack_index[i] = None

        if not data.output_nodes[i]:
            continue
        if not behavior.should_create_base_dot_node(
            source_node, data, i, settings
        ):
            continue

        # Stack the node
        # Create base dot node
        dot_node = StraightenNode(
            source_node.graph.newNode("sbs::compositing::passthrough"),
            source_node.graph,
        )
        data.base_dot_node[i] = dot_node

        pos = Float2(
            source_node.pos.x + settings.dot_node_distance,
            source_node.pos.y + (STRIDE * stack_index),
        )
        dot_node.set_position(pos.x, pos.y)
        _connect_node(source_node, dot_node, data.connection[i][0])
        source_node.output_dot_node = dot_node

        # data.stack_index[i] = stack_index
        stack_index += 1

        # Reconnect all the target nodes
        for j, con in enumerate(data.connection[i]):
            target_node = data.output_nodes[i][j]
            if target_node.pos.x >= source_node.pos.x + settings.dot_node_distance * 2:
                _connect_node(dot_node, target_node, con)


def _insert_target_dot_nodes(
    source_node: StraightenNode,
    data: StraightenConnectionData,
    behavior: AbstractStraightenBehavior,
    settings: StraightenSettings,
):
    already_processed = list()
    for i, _ in enumerate(source_node.output_connectable_properties):
        if not data.output_nodes[i]:
            continue

        if data.base_dot_node[i] is None:
            dot_node = source_node
        else:
            dot_node = data.base_dot_node[i]

        for y, output_node in enumerate(data.output_nodes[i]):
            if behavior.should_create_target_dot_node(
                dot_node, output_node, data, i, settings
            ):
                new_dot_node = StraightenNode(
                    source_node.graph.newNode("sbs::compositing::passthrough"),
                    source_node.graph,
                )
                new_dot_node_pos: Float2 = behavior.get_position_target_dot(
                    dot_node,
                    output_node,
                    data,
                    i,
                    settings,
                )
                new_dot_node.set_position(
                    new_dot_node_pos.x, new_dot_node_pos.y
                )
                _connect_node(dot_node, new_dot_node, data.connection[i][y])

                dot_node.output_dot_node = new_dot_node
                dot_node = new_dot_node
            
            if output_node.pos.x >= dot_node.pos.x + settings.dot_node_distance:
                _connect_node(dot_node, output_node, data.connection[i][y])
            # if output_node not in already_processed:
            #     already_processed.append(output_node)
            
            # Reconnect all the output nodes in front
            # This must be done so the API is aware of the changes
            # Attempting to get indices in target for example
            for y, output_node in enumerate(data.output_nodes[i][y:]):

                if output_node not in already_processed and output_node.pos.x >= dot_node.pos.x + settings.dot_node_distance:
                    _connect_node(dot_node, output_node, data.connection[i][y])
  


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
            try:
                node = StraightenNode(node, api.current_graph)
            except AttributeError:
                # Occurs if the dot node was previously removed
                continue

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


def on_graph_view_created(_, api: APITool):
    settings = StraightenSettings(
        Path(__file__).parent / "bw_straighten_connection_settings.json"
    )
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
