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
from PySide2.QtGui import QIcon, QKeySequence
from PySide2.QtWidgets import QAction, QMessageBox
from sd.api.sdhistoryutils import SDHistoryUtils
from sd.tools.graphlayout import snapSDNodes

from .aligner_mainline import BWMainlineAligner
from .aligner_vertical import BWVerticalAligner
from .alignment_behavior import (
    BWVerticalAlignFarthestInput,
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

        self.mainline_additional_offset: Union[int, float] = self.get(
            "Mainline Settings;content;Additional Offset;value"
        )
        self.mainline_min_threshold: int = self.get(
            "Mainline Settings;content;Minimum Threshold;value"
        )
        self.mainline_enabled: bool = self.get(
            "Mainline Settings;content;Enable;value"
        )
        self.alignment_behavior: int = self.get("Input Node Alignment;value")
        self.node_count_warning: int = self.get("Node Count Warning;value")

        self.run_straighten_connection: bool = self.get(
            "Straighten Connection Settings;content;Enable;value"
        )
        self.straighten_connection_behavior: bool = self.get(
            "Straighten Connection Settings;content;Alignment;value"
        )

        self.snap_to_grid: bool = self.get("Snap To Grid;value")


def run_layout(
    node_selection: BWLayoutNodeSelection,
    api: BWAPITool,
    settings: Optional[BWLayoutSettings] = None,
):
    api.log.info("Running layout Graph")

    if settings is None:
        settings = BWLayoutSettings(
            Path(__file__).parent / "bw_layout_graph_settings.json"
        )

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
            behavior = BWVerticalAlignFarthestInput(settings)
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
        bw_straighten_connection.on_clicked_straighten_connection(
            api, behavior
        )

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
        api_nodes = remove_dot_nodes(
            api.current_node_selection, api.current_graph
        )
        node_selection = BWLayoutNodeSelection(api_nodes, api.current_graph)

        settings = BWLayoutSettings(
            Path(__file__).parent / "bw_layout_graph_settings.json"
        )
        if node_selection.node_count >= settings.node_count_warning:
            msg = (
                "Running Layout Graph on a large selection could take a while,"
                " are you sure you want to continue"
            )
            ret = QMessageBox.question(
                None,
                "",
                msg,
                QMessageBox.Yes | QMessageBox.No,
            )

            if ret == QMessageBox.No:
                return

        run_layout(node_selection, api, settings)


def on_graph_view_created(graph_view_id, api: BWAPITool):
    # toolbar = api.get_graph_view_toolbar(graph_view_id)
    # if toolbar is None:
    toolbar = api.create_graph_view_toolbar(graph_view_id)

    icon_path = Path(__file__).parent / "resources/icons/bwLayoutGraphIcon.png"
    action: QAction = toolbar.addAction(QIcon(str(icon_path.resolve())), "")

    settings = BWLayoutSettings(
        Path(__file__).parent / "bw_layout_graph_settings.json"
    )
    action.setShortcut(QKeySequence(settings.hotkey))
    action.setToolTip("Layout Graph")
    action.triggered.connect(lambda: on_clicked_layout_graph(api))


def on_initialize(api: BWAPITool):
    api.register_on_graph_view_created_callback(
        partial(on_graph_view_created, api=api)
    )


def get_default_settings() -> Dict:
    return {
        "Hotkey": {"widget": 1, "value": "C"},
        "Input Node Alignment": {
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
                "Enable": {"widget": 4, "value": True},
                "Additional Offset": {"widget": 2, "value": 96},
                "Minimum Threshold": {"widget": 2, "value": 96},
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
