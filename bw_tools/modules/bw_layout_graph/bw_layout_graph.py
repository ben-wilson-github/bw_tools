from functools import partial
from pathlib import Path
from typing import List

import sd
from bw_tools.common.bw_api_tool import APITool
from PySide2 import QtGui, QtWidgets

from . import node_sorting, aligner, mainline
from .layout_node import LayoutNode, LayoutNodeSelection

SPACER = 32

# TODO: Create new node selection and node type for this plugin and inherit
# TODO: Add option to reposition roots or not
# TODO: Add option to align by main line
# TODO: Remove dot nodes


def run_layout(node_selection: LayoutNodeSelection, api: APITool):
    api.log.info("Running layout Graph")

    with sd.api.sdhistoryutils.SDHistoryUtils.UndoGroup("Undo Group"):
        api.log.debug("Sorting Nodes...")
        for root_node in node_selection.root_nodes:
            node_sorting.position_nodes(root_node)
        for root_node in node_selection.root_nodes:
            node_sorting.build_alignment_behaviors(root_node)
        
        api.log.debug("Running mainline...")
        mainline.run_mainline(node_selection.branching_input_nodes, node_selection.branching_output_nodes)

        api.log.debug("Aligning Nodes...")
        already_processed = list()
        for root_node in node_selection.root_nodes:
            aligner.run_aligner(root_node, already_processed)

        # api.log.debug("Running mainline")
        # mainline.run_mainline(node_selection.branching_input_nodes, node_selection.branching_output_nodes)
        # already_processed = list()
        # for root_node in node_selection.root_nodes:
        #     aligner.run_aligner(root_node, already_processed)

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
    action.setToolTip("Layout Graph")
    action.triggered.connect(lambda: on_clicked_layout_graph(api))


def on_initialize(api: APITool):
    api.register_on_graph_view_created_callback(
        partial(on_graph_view_created, api=api)
    )


#
# def writeDefaultSettings(aSettingsFilePath):
#     settings = {}
#     settings['hotkey'] = 'c'
#     settings['nodeWidth'] = 96
#     settings['spacer'] = 32
#     settings['selectionCountWarning'] = 30
#     settings['considerSplitNodesForMainline'] = False
#     settings['detailedLog'] = False
#
#     # advancedSettings = {}
#     # advancedSettings['hierarchyPass'] = True
#     # advancedSettings['mainlineLanePass'] = True
#     # advancedSettings['verticalPass'] = True
#     # advancedSettings['secondVerticalPass'] = True
#     # settings['advancedSettings'] = advancedSettings
#
#     with open(aSettingsFilePath) as settingsFile:
#         data = json.load(settingsFile)
#         data['module'][bwSettings.SupportedModules.LayoutGraph.value] = settings
#
#     with open(aSettingsFilePath, 'w') as settingsFile:
#         json.dump(data, settingsFile, indent=4)
#
#
