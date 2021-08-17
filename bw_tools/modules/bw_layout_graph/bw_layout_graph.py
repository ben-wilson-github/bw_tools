from functools import partial
from pathlib import Path

import sd
from bw_tools.common.bw_api_tool import APITool
from PySide2 import QtGui

from . import node_sorting, aligner, mainline
from . import settings
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


def run_layout(node_selection: LayoutNodeSelection, api: APITool):
    api.log.info("Running layout Graph")
    with sd.api.sdhistoryutils.SDHistoryUtils.UndoGroup("Undo Group"):
        api.log.debug("Sorting Nodes...")
        for root_node in node_selection.root_nodes:
            node_sorting.position_nodes(root_node)
        for root_node in node_selection.root_nodes:
            node_sorting.build_alignment_behaviors(root_node)

        api.log.debug("Running mainline...")
        mainline.run_mainline(
            node_selection.branching_input_nodes,
            node_selection.branching_output_nodes,
        )

        api.log.debug("Aligning Nodes...")
        already_processed = list()
        for root_node in node_selection.root_nodes:
            aligner.run_aligner(root_node, already_processed)

        api.log.debug("Positioning API nodes...")
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
    action.setShortcut(
        QtGui.QKeySequence(
            settings.LAYOUT_SETTINGS.get(settings.HOTKEY)
        )
    )
    action.setToolTip("Layout Graph")
    action.triggered.connect(lambda: on_clicked_layout_graph(api))


def on_initialize(api: APITool):
    settings.init()
    api.register_on_graph_view_created_callback(
        partial(on_graph_view_created, api=api)
    )
