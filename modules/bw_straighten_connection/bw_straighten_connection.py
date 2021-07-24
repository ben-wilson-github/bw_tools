import os
import json
from functools import partial
from typing import Tuple
from typing import List
from typing import Any

import sd
from sd.api.sdhistoryutils import SDHistoryUtils
from PySide2 import QtGui

from common import bw_api_tool
from common import bw_node


def node_is_too_close(source_node: sd.api.sdnode.SDNode, target_node: sd.api.sdnode.SDNode, threshold: float) -> bool:
    if source_node.getPosition().x < target_node.getPosition().x - threshold:
        return False
    else:
        return True


def get_from_settings_file(file_path: str, setting: str) -> Any:
    try:
        with open(file_path) as settings_file:
            data = json.load(settings_file)
            ret = data[setting]
    except KeyError:
        raise KeyError(f'Unable to get {setting} from settings file. It was not found inside the file.')

    except FileNotFoundError:
        raise FileNotFoundError(f'Unable to open {file_path}. The file was not found')
    else:
        return ret


def sort_connections_by_position_x(connections: sd.api.sdconnection.SDConnection) -> Tuple[sd.api.sdconnection.SDConnection]:
    sorted_list = list(connections)
    swapped = True
    while swapped:
        swapped = False
        for i in range(len(sorted_list) - 1):
            if sorted_list[i].getInputPropertyNode().getPosition().x == sorted_list[i + 1].getInputPropertyNode().getPosition().x:
                if sorted_list[i].getInputPropertyNode().getPosition().y == sorted_list[i + 1].getInputPropertyNode().getPosition().y:
                    if sorted_list[i].getInputPropertyNode().getIdentifier() > sorted_list[i + 1].getInputPropertyNode().getIdentifier():
                        sorted_list[i], sorted_list[i + 1] = sorted_list[i + 1], sorted_list[i]
                        swapped = True

                elif sorted_list[i].getInputPropertyNode().getPosition().y > sorted_list[i + 1].getInputPropertyNode().getPosition().y:
                    sorted_list[i], sorted_list[i + 1] = sorted_list[i + 1], sorted_list[i]
                    swapped = True
            elif sorted_list[i].getInputPropertyNode().getPosition().x > sorted_list[i + 1].getInputPropertyNode().getPosition().x:
                sorted_list[i], sorted_list[i + 1] = sorted_list[i + 1], sorted_list[i]
                swapped = True
    return tuple(sorted_list)


def insert_dot_node(
        graph: sd.api.sbs.sdsbscompgraph.SDSBSCompGraph,
        source_node: sd.api.sdnode.SDNode,
        source_property: sd.api.sdproperty.SDProperty,
        target_node: sd.api.sdnode.SDNode,
        target_property: sd.api.sdproperty.SDProperty,
        threshold: float
) -> sd.api.sdnode.SDNode:
    dot_node = graph.newNode('sbs::compositing::passthrough')

    source_node.newPropertyConnection(
        source_property,
        dot_node,
        dot_node.getPropertyFromId('input', sd.api.sdproperty.SDPropertyCategory.Input)
    )

    dot_node.newPropertyConnection(
        dot_node.getPropertyFromId('unique_filter_output', sd.api.sdproperty.SDPropertyCategory.Output),
        target_node,
        target_property
    )

    position_at_source = get_from_settings_file(__file__.replace('.py', '_settings.json'), 'Position At Source')
    if position_at_source:
        x = bw_node.Node(source_node).pos.x + threshold
        y = bw_node.Node(target_node).y_position_of_property(target_property)
    else:
        x = bw_node.Node(target_node).pos.x - threshold
        y = bw_node.Node(source_node).y_position_of_property(source_property)

    dot_node.setPosition(
        sd.api.sdbasetypes.float2(
            x,
            y
        )
    )
    return dot_node


def is_dot_node(node : sd.api.sdnode.SDNode) -> bool:
    return node.getDefinition().getId() == 'sbs::compositing::passthrough'


def get_connections_for_node_property(
        graph: sd.api.sbs.sdsbscompgraph.SDSBSCompGraph,
        source_node: sd.api.sdnode.SDNode,
        source_node_property: sd.api.sdproperty.SDProperty
) -> List[sd.api.sdconnection.SDConnection]:
    def already_seen(src, ret):
        for c in ret:
            if c.getInputPropertyNode().getIdentifier() == src.getInputPropertyNode().getIdentifier() \
                    and c.getInputProperty().getId() == src.getInputProperty().getId():
                return True
        return False

    ret = list()
    for connection in source_node.getPropertyConnections(source_node_property):
        next_node_in_chain = connection.getInputPropertyNode()
        if is_dot_node(next_node_in_chain):
            ret += get_connections_for_node_property(
                graph,
                next_node_in_chain,
                next_node_in_chain.getPropertyFromId('unique_filter_output', sd.api.sdproperty.SDPropertyCategory.Output))
            graph.deleteNode(connection.getInputPropertyNode())
        else:
            if already_seen(connection, ret):
                continue
            ret.append(connection)

    # ret = list()
    # for p in source_node.getProperties(sd.api.sdproperty.SDPropertyCategory.Output):
    #     if not p.isConnectable():
    #         continue
    #     for connection in source_node.getPropertyConnections(p):
    #         if is_dot_node(connection.getInputPropertyNode()):
    #             ret += get_connections_for_node_property(graph, connection.getInputPropertyNode())
    #             graph.deleteNode(connection.getInputPropertyNode())
    #         else:
    #             if already_seen(connection, ret):
    #                 continue
    #             ret.append(connection)
    return ret


def straighten_connection(
        source_node: sd.api.sdnode.SDNode,
        source_node_property: sd.api.sdproperty.SDProperty,
        api: bw_api_tool.APITool):

    threshold = get_from_settings_file(__file__.replace('.py', '_settings.json'), 'Distance From Node')

    connections = get_connections_for_node_property(api.current_graph, source_node, source_node_property)
    sorted_connections = sort_connections_by_position_x(connections)

    dot_node = None
    for connection in sorted_connections:
        if dot_node is None:    # On first iteration
            if node_is_too_close(source_node, connection.getInputPropertyNode(), threshold):
                continue
            else:
                dot_node = insert_dot_node(
                    api.current_graph,
                    source_node,
                    source_node_property,
                    connection.getInputPropertyNode(),
                    connection.getInputProperty(),
                    threshold
                )
        else:
            if node_is_too_close(dot_node, connection.getInputPropertyNode(), threshold + (threshold / 2)):
                dot_node.newPropertyConnection(
                    dot_node.getPropertyFromId('unique_filter_output', sd.api.sdproperty.SDPropertyCategory.Output),
                    connection.getInputPropertyNode(),
                    connection.getInputProperty()
                )
            else:
                dot_node = insert_dot_node(
                    api.current_graph,
                    dot_node,
                    dot_node.getPropertyFromId('unique_filter_output', sd.api.sdproperty.SDPropertyCategory.Output),
                    connection.getInputPropertyNode(),
                    connection.getInputProperty(),
                    threshold
                )


def on_clicked_straighten_connection(api: bw_api_tool.APITool):
    with SDHistoryUtils.UndoGroup('Straighten Connection Undo Group'):
        api.logger.info('Running straighten connection')
        node_selection = api.current_selection
        if node_selection is not None:
            for node in node_selection:
                node = bw_node.Node(node)
                for p in node.output_connectable_properties:
                    straighten_connection(node.api_node, p, api)


def on_graph_view_created(_, api: bw_api_tool.APITool):
    icon = os.path.normpath(
        os.path.join(
            os.path.dirname(__file__),
            'resources\\straighten_connection.png'
        )
    )
    action = api.graph_view_toolbar.addAction(QtGui.QIcon(icon), '')
    action.setToolTip('Straighten connections on selected nodes.')
    action.triggered.connect(lambda: on_clicked_straighten_connection(api))

    icon = os.path.normpath(
        os.path.join(
            os.path.dirname(__file__),
            'resources\\remove_dot_node_selected.png'
        )
    )
    action = api.graph_view_toolbar.addAction(QtGui.QIcon(icon), '')
    action.setToolTip('Remove dot nodes from selected nodes.')


def on_initialize(api: bw_api_tool.APITool):
    api.register_on_graph_view_created_callback(partial(on_graph_view_created, api=api))
