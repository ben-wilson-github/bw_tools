from functools import partial
from pathlib import Path
from typing import Optional, Union

import sd
from bw_tools.common import bw_node_selection
from bw_tools.common.bw_api_tool import APITool
from bw_tools.modules.bw_settings.bw_settings import ModuleSettings
from bw_tools.modules.bw_straighten_connection import (
    bw_straighten_connection,
    straighten_behavior,
)
from PySide2 import QtGui, QtWidgets

from . import aligner_mainline, aligner_vertical, node_sorting
from .alignment_behavior import (
    VerticalAlignFarthestInput,
    VerticalAlignMidPoint,
    VerticalAlignTopStack,
)
from .layout_node import LayoutNode, LayoutNodeSelection


class LayoutSettings(ModuleSettings):
    def __init__(self, file_path: Path):
        super().__init__(file_path)
        self.hotkey: str = self.get("Hotkey;value")
        self.node_spacing: Union[int, float] = self.get("Node Spacing;value")
        self.mainline_additional_offset: Union[int, float] = self.get(
            "Mainline Settings;value;Additional Offset;value"
        )
        self.mainline_min_threshold: int = self.get(
            "Mainline Settings;value;Minimum Threshold;value"
        )
        self.mainline_enabled: bool = self.get(
            "Mainline Settings;value;Enable;value"
        )
        self.alignment_behavior: int = self.get("Input Node Alignment;value")
        self.node_count_warning: int = self.get("Node Count Warning;value")
        self.run_straighten_connection: bool = self.get(
            "Straighten Connection Settings;value;Enable;value"
        )
        self.straighten_connection_behavior: bool = self.get(
            "Straighten Connection Settings;value;Alignment;value"
        )
        self.snap_to_grid: bool = self.get("Snap To Grid;value")


def run_layout(
    node_selection: LayoutNodeSelection,
    api: APITool,
    settings: Optional[LayoutSettings] = None,
):
    api.log.info("Running layout Graph")

    if settings is None:
        settings = LayoutSettings(
            Path(__file__).parent / "bw_layout_graph_settings.json"
        )

    node_sorter = node_sorting.NodeSorter(settings)
    for root_node in node_selection.root_nodes:
        node_sorter.position_nodes(root_node)
    for root_node in node_selection.root_nodes:
        node_sorter.build_alignment_behaviors(root_node)

    if settings.mainline_enabled:
        mainline_aligner = aligner_mainline.MainlineAligner(settings)
        mainline_aligner.run_mainline(
            node_selection.branching_input_nodes,
            node_selection.branching_output_nodes,
        )

    already_processed = list()
    for root_node in node_selection.root_nodes:
        if settings.alignment_behavior == 0:
            behavior = VerticalAlignFarthestInput(settings)
        elif settings.alignment_behavior == 1:
            behavior = VerticalAlignMidPoint(settings)
        else:
            behavior = VerticalAlignTopStack(settings)

        vertical_aligner = aligner_vertical.VerticalAligner(settings, behavior)
        vertical_aligner.run_aligner(root_node, already_processed)

    node: LayoutNode
    for node in node_selection.nodes:
        node.set_api_position()

    if settings.snap_to_grid:
        sd.tools.graphlayout.snapSDNodes(api.current_selection)

    if settings.run_straighten_connection:
        if settings.straighten_connection_behavior == 0:
            behavior = straighten_behavior.BreakAtSource(api.current_graph)
        else:
            behavior = straighten_behavior.BreakAtTarget(api.current_graph)
        bw_straighten_connection.on_clicked_straighten_connection(
            api, behavior
        )

    api.log.info("Finished running layout graph")


def on_clicked_layout_graph(api: APITool):
    with sd.api.sdhistoryutils.SDHistoryUtils.UndoGroup("Undo Group"):
        api_nodes = bw_node_selection.remove_dot_nodes(
            api.current_selection, api.current_graph
        )
        node_selection = LayoutNodeSelection(api_nodes, api.current_graph)

        settings = LayoutSettings(
            Path(__file__).parent / "bw_layout_graph_settings.json"
        )
        if node_selection.node_count >= settings.node_count_warning:
            msg = (
                "Running Layout Graph on a large selection could take a while,"
                " are you sure you want to continue"
            )
            ret = QtWidgets.QMessageBox.question(
                None,
                "",
                msg,
                QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
            )

            if ret == QtWidgets.QMessageBox.No:
                return

        run_layout(node_selection, api, settings)


def on_graph_view_created(graph_view_id, api: APITool):
    toolbar = api.get_graph_view_toolbar(graph_view_id)
    if toolbar is None:
        toolbar = api.create_graph_view_toolbar(graph_view_id)

    icon_path = Path(__file__).parent / "resources/icons/bwLayoutGraphIcon.png"
    action = toolbar.addAction(QtGui.QIcon(str(icon_path.resolve())), "")

    settings = LayoutSettings(
        Path(__file__).parent / "bw_layout_graph_settings.json"
    )
    action.setShortcut(QtGui.QKeySequence(settings.hotkey))
    action.setToolTip("Layout Graph")
    action.triggered.connect(lambda: on_clicked_layout_graph(api))


def on_initialize(api: APITool):
    api.register_on_graph_view_created_callback(
        partial(on_graph_view_created, api=api)
    )
