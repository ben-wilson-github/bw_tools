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

import sd
from sd.api.sdhistoryutils import SDHistoryUtils

if TYPE_CHECKING:
    from bw_tools.common.bw_api_tool import APITool


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
    print("sds")


def run_framer(
    nodes: list[SDNode],
    graph_objects: list[SDGraphObject],
    graph: Union[SDSBSCompGraph, SDSBSFunctionGraph],
):
    frames = get_frames(graph_objects)
    print(frames)
    delete_frames(graph, frames)

    x0 = min(nodes, key=lambda node: node.getPosition().x).getPosition().x
    x1 = max(nodes, key=lambda node: node.getPosition().x).getPosition().x
    y0 = max(nodes, key=lambda node: node.getPosition().y).getPosition().y
    y1 = min(nodes, key=lambda node: node.getPosition().y).getPosition().y
    print(x0)
    print(x1)

    CONTINUE HERE

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
