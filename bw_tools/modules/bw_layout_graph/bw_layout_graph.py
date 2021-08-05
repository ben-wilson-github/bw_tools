import importlib
from functools import partial
from pathlib import Path

import sd
from bw_tools.common import bw_api_tool, bw_node, bw_node_selection
from PySide2 import QtGui, QtWidgets

from .layout_node import LayoutNode, LayoutNodeSelection
from . import (
    aligner,
    bw_layout_horizontal,
    bw_layout_mainline,
    chain_aligner,
    node_sorting,
    utils,
    layout_node,
)

importlib.reload(utils)
importlib.reload(layout_node)
importlib.reload(bw_node)
importlib.reload(bw_api_tool)
importlib.reload(node_sorting)
importlib.reload(aligner)
importlib.reload(chain_aligner)
importlib.reload(bw_node_selection)
importlib.reload(bw_layout_mainline)
importlib.reload(bw_layout_horizontal)


SPACER = 32

# TODO: Create new node selection and node type for this plugin and inherit
# TODO: Add option to reposition roots or not
# TODO: Add option to align by main line
# TODO: Remove dot nodes


def run_layout(
    node_selection: bw_node_selection.NodeSelection, api: bw_api_tool.APITool
):
    api.log.info("Running layout Graph")

    with sd.api.sdhistoryutils.SDHistoryUtils.UndoGroup("Undo Group"):

        api.log.debug("Sorting Nodes...")
        already_processed = list()
        for node_chain in node_selection.node_chains:
            if node_chain.root.output_node_count != 0:
                continue
            node_sorting.run_sort(node_chain.root, already_processed)

        api.log.debug("Aligning Nodes...")
        already_processed = list()
        roots_to_update = list()
        for node_chain in node_selection.node_chains:
            if node_chain.root.output_node_count != 0:
                continue
            aligner.run_aligner(
                node_chain.root,
                already_processed,
                roots_to_update,
                node_selection,
            )


def on_clicked_layout_graph(api: bw_api_tool):
    node_selection = LayoutNodeSelection(
        api.current_selection, api.current_graph
    )
    print(node_selection)
    run_layout(node_selection, api)


def on_graph_view_created(_, api: bw_api_tool.APITool):
    icon_path = Path(__file__).parent / "resources/icons/bwLayoutGraphIcon.png"
    action = api.graph_view_toolbar.addAction(
        QtGui.QIcon(str(icon_path.resolve())), ""
    )
    action.setToolTip("Layout Graph")
    action.triggered.connect(lambda: on_clicked_layout_graph(api))


def on_initialize(api: bw_api_tool.APITool):
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
