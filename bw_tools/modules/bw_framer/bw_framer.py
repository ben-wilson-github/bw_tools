from __future__ import annotations

import os
from functools import partial
from pathlib import Path
from typing import TYPE_CHECKING, Dict

from bw_tools.common.bw_node import BWNode
from bw_tools.modules.bw_settings.bw_settings import BWModuleSettings
from PySide2 import QtGui
from PySide2.QtWidgets import QAction
from sd.api import sdbasetypes
from sd.api.sdgraph import SDGraph
from sd.api.sdgraphobject import SDGraphObject
from sd.api.sdgraphobjectframe import SDGraphObjectFrame
from sd.api.sdhistoryutils import SDHistoryUtils
from sd.api.sdnode import SDNode

if TYPE_CHECKING:
    from bw_tools.common.bw_api_tool import BWAPITool


class BWFramerSettings(BWModuleSettings):
    def __init__(self, file_path: Path):
        super().__init__(file_path)
        self.hotkey: str = self.get("Hotkey;value")
        self.margin: float = self.get("Margin;value")
        self.default_color: list = self.get("Default Color;value")
        self.default_title: str = self.get("Default Title;value")
        self.default_description: str = self.get("Default Description;value")


def get_frames(graph_objects: list[SDGraphObject]) -> list[SDGraphObjectFrame]:
    return [
        obj for obj in graph_objects if isinstance(obj, SDGraphObjectFrame)
    ]


def delete_frames(
    graph: SDGraph,
    frames: list[SDGraphObjectFrame],
):
    [graph.deleteGraphObject(frame) for frame in frames]


def run_framer(
    nodes: list[SDNode],
    graph_objects: list[SDGraphObject],
    graph: SDGraph,
    settings: BWFramerSettings,
):
    x0 = min(nodes, key=lambda node: node.getPosition().x)
    x1 = max(nodes, key=lambda node: node.getPosition().x)
    y0 = max(nodes, key=lambda node: node.getPosition().y)
    y1 = min(nodes, key=lambda node: node.getPosition().y)

    x0 = BWNode(x0)
    x1 = BWNode(x1)
    y0 = BWNode(y0)
    y1 = BWNode(y1)

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
        frame: SDGraphObjectFrame = SDGraphObjectFrame.sNew(graph)
        frame.setTitle(settings.default_title)
        frame.setColor(
            sdbasetypes.ColorRGBA(
                settings.default_color[0],
                settings.default_color[1],
                settings.default_color[2],
                settings.default_color[3],
            )
        )
        frame.setDescription(settings.default_description)

    frame.setPosition(
        sdbasetypes.float2(
            min_x - settings.margin, min_y - settings.margin * 2
        )
    )
    frame.setSize(sdbasetypes.float2(width, height))


def on_clicked_run_framer(api: BWAPITool):
    pkg = api.current_package
    file_path = Path(pkg.getFilePath())
    if not os.access(file_path, os.W_OK):
        return

    with SDHistoryUtils.UndoGroup("Framer"):
        settings = BWFramerSettings(
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


def on_graph_view_created(graph_view_id, api: BWAPITool):
    toolbar = api.get_graph_view_toolbar(graph_view_id)
    if toolbar is None:
        toolbar = api.create_graph_view_toolbar(graph_view_id)

    settings = BWFramerSettings(
        Path(__file__).parent / "bw_framer_settings.json"
    )

    icon = Path(__file__).parent / "resources" / "bw_framer_icon.png"
    action: QAction = toolbar.addAction(QtGui.QIcon(str(icon.resolve())), "")
    action.setShortcut(QtGui.QKeySequence(settings.hotkey))
    action.setToolTip("Frames the selected nodes")
    action.triggered.connect(lambda: on_clicked_run_framer(api))


def on_initialize(api: BWAPITool):
    api.register_on_graph_view_created_callback(
        partial(on_graph_view_created, api=api)
    )


def get_default_settings() -> Dict:
    return {
        "Hotkey": {"widget": 1, "value": "Alt+D"},
        "Margin": {"widget": 2, "value": 32},
        "Default Color": {"widget": 6, "value": [0.0, 0.0, 0.0, 0.25]},
        "Default Title": {"widget": 1, "value": ""},
        "Default Description": {"widget": 1, "value": ""}
    }
