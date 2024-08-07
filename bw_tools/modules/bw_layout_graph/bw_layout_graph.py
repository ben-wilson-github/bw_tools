import os
from functools import partial
from pathlib import Path
from typing import Dict, Optional, Union

from bw_tools.common.bw_api_tool import BWAPITool
from bw_tools.common.bw_node_selection import remove_dot_nodes
from bw_tools.modules.bw_settings.bw_settings import BWModuleSettings
from bw_tools.modules.bw_straighten_connection import bw_straighten_connection
from bw_tools.modules.bw_straighten_connection.straighten_behavior import (
    BWBreakAtSource,
    BWBreakAtTarget,
)
from PySide6.QtGui import QIcon, QKeySequence, QAction
from PySide6.QtWidgets import QMessageBox
from sd.api.sdhistoryutils import SDHistoryUtils
from sd.tools.graphlayout import snapSDNodes

from .aligner_mainline import BWMainlineAligner
from .aligner_vertical import BWVerticalAligner
from .alignment_behavior import (
    BWVerticalAlignMainlineInput,
    BWVerticalAlignMidPoint,
    BWVerticalAlignTopStack,
)
from .layout_node import BWLayoutNode, BWLayoutNodeSelection
from .node_sorting import BWNodeSorter


class BWLayoutSettings(BWModuleSettings):
    def __init__(self, file_path: Path):
        super().__init__(file_path)
        self.hotkey: str = self.get("Hotkey;value")
        self.node_spacing: Union[int, float] = self.get("Node Spacing;value")
        self.mainline_additional_offset: Union[int, float] = self.get("Mainline Settings;content;Offset Amount;value")
        self.mainline_min_threshold: int = self.get("Mainline Settings;content;Adjacent Chain Threshold;value")
        self.mainline_enabled: bool = self.get("Mainline Settings;content;Enable Offset Mainline;value")
        self.alignment_behavior: int = self.get("Vertical Alignment;value")
        self.node_count_warning: int = self.get("Node Count Warning;value")

        self.run_straighten_connection: bool = self.get("Straighten Connection Settings;content;Enable;value")
        self.straighten_connection_behavior: bool = self.get("Straighten Connection Settings;content;Alignment;value")

        self.snap_to_grid: bool = self.get("Snap To Grid;value")


def run_layout(
    node_selection: BWLayoutNodeSelection,
    api: BWAPITool,
    settings: Optional[BWLayoutSettings] = None,
):
    api.log.info("Running layout Graph")

    if settings is None:
        settings = BWLayoutSettings(Path(__file__).parent / "bw_layout_graph_settings.json")

    node_sorter = BWNodeSorter(settings)
    for root_node in node_selection.root_nodes:
        node_sorter.position_nodes(root_node)
    for root_node in node_selection.root_nodes:
        node_sorter.build_alignment_behaviors(root_node)

    if settings.mainline_enabled:
        mainline_aligner = BWMainlineAligner(settings)
        mainline_aligner.run_mainline(
            node_selection.branching_input_nodes,
            node_selection.branching_output_nodes,
        )

    already_processed = list()
    for root_node in node_selection.root_nodes:
        if settings.alignment_behavior == "Mainline":
            behavior = BWVerticalAlignMainlineInput(settings)
        elif settings.alignment_behavior == "Center":
            behavior = BWVerticalAlignMidPoint(settings)
        else:
            behavior = BWVerticalAlignTopStack(settings)

        vertical_aligner = BWVerticalAligner(settings, behavior)
        vertical_aligner.run_aligner(root_node, already_processed)

    node: BWLayoutNode
    for node in node_selection.nodes:
        node.set_api_position()

    if settings.snap_to_grid:
        snapSDNodes(api.current_node_selection)

    if settings.run_straighten_connection:
        if settings.straighten_connection_behavior == 0:
            behavior = BWBreakAtSource(api.current_graph)
        else:
            behavior = BWBreakAtTarget(api.current_graph)
        bw_straighten_connection.on_clicked_straighten_connection(api, behavior)

    api.log.info("Finished running layout graph")


def on_clicked_layout_graph(api: BWAPITool):
    if not api.current_graph_is_supported:
        api.log.error("Graph type is unsupported")
        return

    pkg = api.current_package
    file_path = Path(pkg.getFilePath())
    if not os.access(file_path, os.W_OK):
        api.log.error("Permission denied to write to package")
        return

    with SDHistoryUtils.UndoGroup("Undo Group"):
        settings = BWLayoutSettings(Path(__file__).parent / "bw_layout_graph_settings.json")
        if len(api.current_node_selection) >= settings.node_count_warning:
            msg = "Running Layout Graph on a large selection could take a while," " are you sure you want to continue"
            ret = QMessageBox.question(
                None,
                "",
                msg,
                QMessageBox.Yes | QMessageBox.No,
            )

            if ret == QMessageBox.No:
                return

        api_nodes = remove_dot_nodes(api.current_node_selection, api.current_graph)
        node_selection = BWLayoutNodeSelection(api_nodes, api.current_graph)

        run_layout(node_selection, api, settings)


def on_graph_view_created(graph_view_id, api: BWAPITool):
    toolbar = api.get_graph_view_toolbar(graph_view_id)

    settings = BWLayoutSettings(Path(__file__).parent / "bw_layout_graph_settings.json")

    icon_path = Path(__file__).parent / "resources/icons/bwLayoutGraphIcon.png"
    tooltip = f"""
    Automatically align selected nodes based on their hierarchy, arranged
    to minimise overlapping. Align a given nodes inputs about their center
    point, stack them on top of each other or align them by their mainline.

    Shortcut: {settings.hotkey}
    """
    action = QAction()
    action.setIcon(QIcon(str(icon_path.resolve())))
    action.setShortcut(QKeySequence(settings.hotkey))
    action.setToolTip(tooltip)
    action.triggered.connect(lambda: on_clicked_layout_graph(api))
    toolbar.add_action("bw_layout_graph", action)


def on_initialize(api: BWAPITool):
    api.register_on_graph_view_created_callback(partial(on_graph_view_created, api=api))


def get_default_settings() -> Dict:
    return {
        "Hotkey": {"widget": 1, "value": "C"},
        "Vertical Alignment": {
            "widget": 5,
            "list": ["Mainline", "Center", "Top"],
            "value": "Mainline",
        },
        "Node Spacing": {"widget": 2, "value": 32},
        "Node Count Warning": {"widget": 2, "value": 80},
        "Snap To Grid": {"widget": 4, "value": False},
        "Mainline Settings": {
            "widget": 0,
            "content": {
                "Enable Offset Mainline": {"widget": 4, "value": True},
                "Offset Amount": {"widget": 2, "value": 96},
                "Adjacent Chain Threshold": {"widget": 2, "value": 128},
            },
        },
        "Straighten Connection Settings": {
            "widget": 0,
            "content": {
                "Enable": {"widget": 4, "value": True},
                "Alignment": {
                    "widget": 5,
                    "list": ["Break At Source", "Break At Target"],
                    "value": "Break At Target",
                },
            },
        },
    }
