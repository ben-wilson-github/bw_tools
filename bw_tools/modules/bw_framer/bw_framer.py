from __future__ import annotations
from bw_tools.common.bw_api_tool import (
    SDGraphObject,
    SDGraphObjectFrame,
    SDNode,
    SDSBSCompGraph,
    SDSBSFunctionGraph,
)

from functools import partial
from typing import TYPE_CHECKING, Union
from bw_tools.common.bw_node import Node

import sd
from sd.api.sdhistoryutils import SDHistoryUtils

if TYPE_CHECKING:
    from bw_tools.common.bw_api_tool import APITool

SPACER = 32
DEFAULT_COLOR = (0.0, 0.0, 0.0, 0.25)

# class StraightenSettings(ModuleSettings):
#     def __init__(self, file_path: Path):
#         super().__init__(file_path)
#         self.target_hotkey: str = self.get("Break At Target Hotkey;value")
#         self.source_hotkey: str = self.get("Break At Source Hotkey;value")
#         self.remove_dot_nodes_hotkey: str = self.get(
#             "Remove Connected Dot Nodes Hotkey;value"
#         )
#         self.dot_node_distance: str = self.get("Dot Node Distance;value")


def get_frames(graph_objects: list[SDGraphObject]) -> list[SDGraphObjectFrame]:
    return [
        obj
        for obj in graph_objects
        if isinstance(obj, sd.api.sdgraphobjectframe.SDGraphObjectFrame)
    ]


def delete_frames(
    graph: Union[SDSBSCompGraph, SDSBSFunctionGraph],
    frames: list[SDGraphObjectFrame],
):
    [graph.deleteGraphObject(frame) for frame in frames]


def run_framer(
    nodes: list[SDNode],
    graph_objects: list[SDGraphObject],
    graph: Union[SDSBSCompGraph, SDSBSFunctionGraph],
):
    x0 = min(nodes, key=lambda node: node.getPosition().x)
    x1 = max(nodes, key=lambda node: node.getPosition().x)
    y0 = max(nodes, key=lambda node: node.getPosition().y)
    y1 = min(nodes, key=lambda node: node.getPosition().y)

    x0 = Node(x0)
    x1 = Node(x1)
    y0 = Node(y0)
    y1 = Node(y1)

    min_x = x0.pos.x - x0.width / 2
    max_x = x1.pos.x - x1.width / 2
    min_y = y1.pos.y - y1.width / 2
    max_y = y0.pos.y - y0.width / 2
    width = (max_x - min_x) + x1.width + SPACER * 2
    height = (max_y - min_y) + y0.height + SPACER * 3

    frames = get_frames(graph_objects)
    if frames:
        frames.sort(key=lambda f: f.getPosition().x)
        frame = frames[0]
        delete_frames(graph, frames[1:])
    else:
        frame = sd.api.sdgraphobjectframe.SDGraphObjectFrame.sNew(graph)

    frame.setPosition(
        sd.api.sdbasetypes.float2(min_x - SPACER, min_y - SPACER * 2)
    )
    frame.setSize(sd.api.sdbasetypes.float2(width, height))
    frame.setColor(sd.api.sdbasetypes.ColorRGBA(0.0, 0.0, 0.0, 0.25))


def on_clicked_run_framer(api: APITool):
    with SDHistoryUtils.UndoGroup("Framer"):
        nodes = api.current_node_selection
        if len(nodes) == 0:
            return
        run_framer(
            nodes, api.current_graph_object_selection, api.current_graph
        )


def on_graph_view_created(graph_view_id, api: APITool):
    toolbar = api.get_graph_view_toolbar(graph_view_id)
    if toolbar is None:
        toolbar = api.create_graph_view_toolbar(graph_view_id)

    # settings = StraightenSettings(
    #     Path(__file__).parent / "bw_straighten_connection_settings.json"
    # )

    # icon = (
    #     Path(__file__).parent
    #     / "resources"
    #     / "straighten_connection_source.png1"
    # )
    # action = toolbar.addAction(QtGui.QIcon(str(icon.resolve())), "")
    action = toolbar.addAction("Framer")
    # action.setShortcut(QtGui.QKeySequence(settings.source_hotkey))
    action.setToolTip("Reframes the selected nodes")
    action.triggered.connect(lambda: on_clicked_run_framer(api))


def on_initialize(api: APITool):
    api.register_on_graph_view_created_callback(
        partial(on_graph_view_created, api=api)
    )
