from __future__ import annotations

import os
from dataclasses import dataclass, field
from functools import partial
from pathlib import Path
from typing import TYPE_CHECKING, Dict, List, Type

from bw_tools.common.bw_api_tool import CompNodeID, FunctionNodeId
from bw_tools.common.bw_node import BWFloat2
from bw_tools.modules.bw_settings.bw_settings import BWModuleSettings
from PySide2.QtGui import QIcon, QKeySequence
from PySide2.QtWidgets import QAction
from sd.api.sbs.sdsbsfunctiongraph import SDSBSFunctionGraph
from sd.api.sdconnection import SDConnection
from sd.api.sdgraph import SDGraph
from sd.api.sdhistoryutils import SDHistoryUtils
from sd.api.sdproperty import SDProperty, SDPropertyCategory

from .straighten_behavior import BWBreakAtSource, BWBreakAtTarget
from .straighten_node import BWStraightenNode

if TYPE_CHECKING:
    from bw_tools.common.bw_api_tool import BWAPITool

    from .straighten_behavior import BWAbstractStraightenBehavior


STRIDE = 21.33  # Magic number between each input slot


class BWStraightenSettings(BWModuleSettings):
    def __init__(self, file_path: Path):
        super().__init__(file_path)
        self.target_hotkey: str = self.get("Break At Target Hotkey;value")
        self.source_hotkey: str = self.get("Break At Source Hotkey;value")
        self.remove_dot_nodes_hotkey: str = self.get(
            "Remove Connected Dot Nodes Hotkey;value"
        )
        self.dot_node_distance: str = self.get("Dot Node Distance;value")


@dataclass
class BWStraightenConnectionData:
    connection: Dict[int, List[SDConnection]] = field(default_factory=dict)
    base_dot_node: Dict[int, BWStraightenNode] = field(default_factory=dict)
    properties_with_outputs_count: int = 0
    output_nodes: Dict[int, List[BWStraightenNode]] = field(
        default_factory=dict
    )


def run_straighten_connection(
    node: BWStraightenNode,
    behavior: BWAbstractStraightenBehavior,
    settings: BWStraightenSettings,
):
    """
    Create and position a series of dot nodes from source node to each
    connected output node. Dot node alignment is determined by a given
    behavior and its settings.
    """
    node.delete_output_dot_nodes()
    data = _create_connection_data_for_all_inputs(node)
    _create_base_dot_nodes(node, data, behavior, settings)
    _align_base_dot_nodes(node, data, behavior, settings)
    _insert_target_dot_nodes(node, data, behavior, settings)


def _align_base_dot_nodes(
    source_node: BWStraightenNode,
    data: BWStraightenConnectionData,
    behavior: Type[BWAbstractStraightenBehavior],
    settings: BWStraightenSettings,
):
    for i, _ in enumerate(source_node.output_connectable_properties):
        if data.base_dot_node[i] is None:
            continue
        behavior.align_base_dot_node(source_node, data, i, settings)


def _create_connection_data_for_all_inputs(
    source_node: BWStraightenNode,
) -> BWStraightenConnectionData:
    """
    Create and return generic data about the output connections.
    StraightenConnectionData.output_nodes will be ordered by position x
    """
    data = BWStraightenConnectionData()
    for i, api_property in enumerate(
        source_node.output_connectable_properties
    ):
        cons = source_node._get_connected_output_connections_for_property(
            api_property
        )
        cons.sort(key=lambda c: c.getInputPropertyNode().getPosition().x)
        data.output_nodes[i] = [
            BWStraightenNode(con.getInputPropertyNode(), source_node.graph)
            for con in cons
        ]
        data.connection[i] = cons
        if cons:
            data.properties_with_outputs_count += 1
    return data


def _create_base_dot_nodes(
    source_node: BWStraightenNode,
    data: BWStraightenConnectionData,
    behavior: Type[BWAbstractStraightenBehavior],
    settings: BWStraightenSettings,
):
    """
    Creates dot nodes near the initial source node for every output
    connection. This is done first so additional alignment logic can
    easily be calculated, such as aligning dot nodes to source node
    center.

    The result of this pass will be dot nodes stacked on top of each
    other, running downwards, starting from the source position y.
    """
    # Store initial bound values
    stack_index = 0
    for i, _ in enumerate(source_node.output_connectable_properties):
        data.base_dot_node[i] = None

        if not data.output_nodes[i]:
            continue
        if not behavior.should_create_base_dot_node(
            source_node, data, i, settings
        ):
            continue

        dot_node = BWStraightenNode(
            source_node.graph.newNode(
                _get_dot_node_id_for_graph(source_node.graph)
            ),
            source_node.graph,
        )
        data.base_dot_node[i] = dot_node

        pos = BWFloat2(
            source_node.pos.x + settings.dot_node_distance,
            source_node.pos.y + (STRIDE * stack_index),
        )
        dot_node.set_position(pos.x, pos.y)
        _connect_node(source_node, dot_node, data.connection[i][0])

        stack_index += 1


def _get_dot_node_id_for_graph(graph: Type[SDGraph]) -> str:
    if isinstance(graph, SDSBSFunctionGraph):
        return FunctionNodeId.DOT.value
    else:
        return CompNodeID.DOT.value


def _insert_target_dot_nodes(
    source_node: BWStraightenNode,
    data: BWStraightenConnectionData,
    behavior: Type[BWAbstractStraightenBehavior],
    settings: BWStraightenSettings,
):
    """
    Create and position dot nodes starting from the intial base dot node
    running to each output. The alignment behavior determins how the
    dot nodes are positioned.

    The dot nodes are created one output at a time and in order from closest
    to farthest. Additionally, new connections will reuse existing dot nodes
    if required. This means alignment behavior logic can not make any
    assumptions about output nodes infront it. For example, making API calls
    to determin how many outputs are connected to a newly created dot node
    will not work, since not all the outputs may not have been processed yet.
    The other outputs would still be connected to the source node.
    """
    for i, _ in enumerate(source_node.output_connectable_properties):
        if not data.output_nodes[i]:
            continue

        if data.base_dot_node[i] is None:
            dot_node = source_node
        else:
            dot_node = data.base_dot_node[i]

        for y, output_node in enumerate(data.output_nodes[i]):

            if behavior.should_create_target_dot_node(
                source_node, dot_node, output_node, data, i, settings
            ):
                new_dot_node = BWStraightenNode(
                    source_node.graph.newNode(
                        _get_dot_node_id_for_graph(source_node.graph)
                    ),
                    source_node.graph,
                )
                new_dot_node_pos: BWFloat2 = behavior.get_position_target_dot(
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

                dot_node = new_dot_node

            if (
                output_node.pos.x
                >= dot_node.pos.x + settings.dot_node_distance
            ):
                _connect_node(dot_node, output_node, data.connection[i][y])


def _connect_node(
    source_node: BWStraightenNode,
    target_node: BWStraightenNode,
    connection: SDConnection,
):
    """
    Helper function to connect a node to another. Uses the given connection
    to determin which property the new connection should be made too.
    """
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
    target_node: BWStraightenNode, connection: SDConnection
) -> SDProperty:
    if target_node.is_dot:
        return target_node.api_node.getPropertyFromId(
            "input", SDPropertyCategory.Input
        )
    return connection.getInputProperty()


def _get_source_property_from_connection(
    source_node: BWStraightenNode, connection: SDConnection
) -> SDProperty:
    if source_node.is_dot:
        return source_node.api_node.getPropertyFromId(
            "unique_filter_output",
            SDPropertyCategory.Output,
        )
    return connection.getOutputProperty()


def on_clicked_straighten_connection(
    api: BWAPITool, behavior: Type[BWAbstractStraightenBehavior]
):
    if not api.current_graph_is_supported:
        api.log.error("Graph type is unsupported")
        return

    pkg = api.current_package
    file_path = Path(pkg.getFilePath())
    if not os.access(file_path, os.W_OK):
        api.log.error("Permission denied to write to package")
        return

    with SDHistoryUtils.UndoGroup("Straighten Connection Undo Group"):
        api.logger.info("Running straighten connection")

        settings = BWStraightenSettings(
            Path(__file__).parent / "bw_straighten_connection_settings.json"
        )

        for node in api.current_node_selection:
            try:
                node = BWStraightenNode(node, api.current_graph)
            except AttributeError:
                # Occurs if the dot node was previously removed
                continue
            run_straighten_connection(node, behavior, settings)


def on_clicked_remove_dot_nodes_from_selection(api: BWAPITool):
    if not api.current_graph_is_supported:
        api.log.error("Graph type is unsupported")
        return

    pkg = api.current_package
    file_path = Path(pkg.getFilePath())
    if not os.access(file_path, os.W_OK):
        return

    with SDHistoryUtils.UndoGroup("Remove Dot Nodes Undo Group"):
        api.logger.info("Running remove dot nodes from selection")

        for node in api.current_node_selection:
            try:
                node = BWStraightenNode(node, api.current_graph)
            except AttributeError:
                continue

            node.delete_output_dot_nodes()


def on_graph_view_created(graph_view_id, api: BWAPITool):
    api.add_toolbar_to_graph_view(graph_view_id)

    settings = BWStraightenSettings(
        Path(__file__).parent / "bw_straighten_connection_settings.json"
    )

    icon = (
        Path(__file__).parent
        / "resources"
        / "straighten_connection_target.png"
    )
    tooltip = f"""
    Straightens connection from selected nodes to all outputs by inserting
    dot nodes into the connection.

    Connections align horiontally to the source node.

    Shortcut: {settings.target_hotkey}
    """
    action = QAction()
    action.setIcon(QIcon(str(icon.resolve())))
    action.setToolTip(tooltip)
    action.setShortcut(QKeySequence(settings.target_hotkey))
    action.triggered.connect(
        lambda: on_clicked_straighten_connection(
            api, BWBreakAtTarget(api.current_graph)
        )
    )
    api.graph_view_toolbar.add_action("bw_straighten_target", action)

    icon = (
        Path(__file__).parent
        / "resources"
        / "straighten_connection_source.png"
    )
    tooltip = f"""
    Straightens connection from selected nodes to all outputs by inserting
    dot nodes into the connection.

    Connections align horizontally to the y center of all output nodes.

    Shortcut: {settings.source_hotkey}
    """
    action = QAction()
    action.setIcon(QIcon(str(icon.resolve())))
    action.setToolTip(tooltip)
    action.setShortcut(QKeySequence(settings.source_hotkey))
    action.triggered.connect(
        lambda: on_clicked_straighten_connection(
            api, BWBreakAtSource(api.current_graph)
        )
    )
    api.graph_view_toolbar.add_action("bw_straighten_source", action)

    icon = Path(__file__).parent / "resources" / "remove_dot_node_selected.png"
    tooltip = f"""
    Remove all dot nodes connected to the outputs of the selected nodes.

    Shortcut: {settings.remove_dot_nodes_hotkey}
    """
    action = QAction()
    action.setIcon(QIcon(str(icon.resolve())))
    action.setToolTip(tooltip)
    action.setShortcut(QKeySequence(settings.remove_dot_nodes_hotkey))
    action.triggered.connect(
        lambda: on_clicked_remove_dot_nodes_from_selection(api)
    )
    api.graph_view_toolbar.add_action("bw_straighten_remove", action)


def on_initialize(api: BWAPITool):
    api.register_on_graph_view_created_callback(
        partial(on_graph_view_created, api=api)
    )


def get_default_settings() -> Dict:
    return {
        "Break At Target Hotkey": {"widget": 1, "value": "Alt+C"},
        "Break At Source Hotkey": {"widget": 1, "value": "Alt+V"},
        "Remove Connected Dot Nodes Hotkey": {"widget": 1, "value": "Alt+X"},
        "Dot Node Distance": {"widget": 2, "value": 196},
    }
