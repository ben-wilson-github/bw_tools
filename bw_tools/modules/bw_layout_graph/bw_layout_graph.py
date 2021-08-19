from functools import partial
from pathlib import Path
from typing import Union

import sd
from bw_tools.common.bw_api_tool import APITool
from bw_tools.modules.bw_settings.bw_settings import ModuleSettings
from PySide2 import QtGui

from . import aligner_vertical, aligner_mainline, node_sorting
from .alignment_behavior import VerticalAlignFarthestInput
from .layout_node import LayoutNode, LayoutNodeSelection

# TODO: Add option to reposition roots or not
# TODO: Add option to align by main line
# TODO: Remove dot nodes
# TODO: hotkey
# TODO: Spacer
# TODO: spacer for root nodes?
# TODO: settings['selectionCountWarning'] = 30
# TODO: Move unit tests to debug menu
# TODO: Move everything to top menu


class LayoutSettings(ModuleSettings):
    def __init__(self, file_path: Path):
        super().__init__(file_path)
        self.hotkey: str = self.get("Hotkey;value")
        self.node_spacing: Union[int, float] = self.get("Node Spacing;value")
        self.mainline_additional_offset: Union[int, float] = self.get(
            "Mainline Settings;value;Additional Offset;value"
        )
        self.mainline_enabled: bool = self.get(
            "Mainline Settings;value;Enable;value"
        )


def run_layout(node_selection: LayoutNodeSelection, api: APITool):
    api.log.info("Running layout Graph")
    with sd.api.sdhistoryutils.SDHistoryUtils.UndoGroup("Undo Group"):
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
            vertical_aligner = aligner_vertical.VerticalAligner(
                settings, VerticalAlignFarthestInput()
            )
            vertical_aligner.run_aligner(root_node, already_processed)

        node: LayoutNode
        for node in node_selection.nodes:
            node.set_api_position()

    api.log.info("Finished running layout graph")


def on_clicked_layout_graph(api: APITool):
    node_selection = LayoutNodeSelection(
        api.current_selection, api.current_graph
    )
    run_layout(node_selection, api)


def on_graph_view_created(_, api: APITool):
    icon_path = Path(__file__).parent / "resources/icons/bwLayoutGraphIcon.png"
    action = api.graph_view_toolbar.addAction(
        QtGui.QIcon(str(icon_path.resolve())), ""
    )

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
