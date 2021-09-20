from __future__ import annotations

from functools import partial
from pathlib import Path
from typing import TYPE_CHECKING, Union, Dict

import sd
from bw_tools.common.bw_api_tool import (
    SDGraphObject,
    SDGraphObjectFrame,
    SDNode,
    SDSBSCompGraph,
    SDSBSFunctionGraph,
)
from bw_tools.common.bw_node import Node
from bw_tools.modules.bw_settings.bw_settings import ModuleSettings
from PySide2 import QtGui
from sd.api.sdhistoryutils import SDHistoryUtils

if TYPE_CHECKING:
    from bw_tools.common.bw_api_tool import APITool


class FramerSettings(ModuleSettings):
    def __init__(self, file_path: Path):
        super().__init__(file_path)
        self.hotkey: str = self.get("Hotkey;value")
        self.margin: float = self.get("Margin;value")
        self.default_color: list = self.get("Default Color;value")
        self.default_title: str = self.get("Default Title;value")


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
    settings: FramerSettings,
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
    width = (max_x - min_x) + x1.width + settings.margin * 2
    height = (max_y - min_y) + y0.height + settings.margin * 3

    frames = get_frames(graph_objects)
    if frames:
        frames.sort(key=lambda f: f.getPosition().x)
        frame = frames[0]
        delete_frames(graph, frames[1:])
    else:
        frame = sd.api.sdgraphobjectframe.SDGraphObjectFrame.sNew(graph)
        frame.setTitle(settings.default_title)
        frame.setColor(
            sd.api.sdbasetypes.ColorRGBA(
                settings.default_color[0],
                settings.default_color[1],
                settings.default_color[2],
                settings.default_color[3],
            )
        )

    frame.setPosition(
        sd.api.sdbasetypes.float2(
            min_x - settings.margin, min_y - settings.margin * 2
        )
    )
    frame.setSize(sd.api.sdbasetypes.float2(width, height))


def on_clicked_run_framer(api: APITool):
    with SDHistoryUtils.UndoGroup("Framer"):
        settings = FramerSettings(
            Path(__file__).parent / "bw_framer_settings.json"
        )
        nodes = api.current_node_selection
        if len(nodes) == 0:
            return
        run_framer(
            nodes,
            api.current_graph_object_selection,
            api.current_graph,
            settings,
        )


def on_graph_view_created(graph_view_id, api: APITool):
    toolbar = api.get_graph_view_toolbar(graph_view_id)
    if toolbar is None:
        toolbar = api.create_graph_view_toolbar(graph_view_id)

    settings = FramerSettings(
        Path(__file__).parent / "bw_framer_settings.json"
    )

    icon = Path(__file__).parent / "resources" / "bw_framer_icon.png"
    action = toolbar.addAction(QtGui.QIcon(str(icon.resolve())), "")
    action.setShortcut(QtGui.QKeySequence(settings.hotkey))
    action.setToolTip("Frames the selected nodes")
    action.triggered.connect(lambda: on_clicked_run_framer(api))


def on_initialize(api: APITool):
    api.register_on_graph_view_created_callback(
        partial(on_graph_view_created, api=api)
    )


def get_default_settings() -> Dict:
    return {
        "Hotkey": {"widget": 1, "value": "Alt+D"},
        "Margin": {"widget": 2, "value": 32},
        "Default Color": {"widget": 6, "value": [0.0, 0.0, 0.0, 0.25]},
        "Default Title": {"widget": 1, "value": ""},
    }
