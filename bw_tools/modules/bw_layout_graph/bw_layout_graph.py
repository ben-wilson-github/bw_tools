import importlib
import math
import os
from functools import partial
from pathlib import Path

import sd
from bw_tools.common import bw_api_tool, bw_node, bw_node_selection
from PySide2 import QtGui, QtWidgets

from . import (aligner, bw_layout_horizontal, bw_layout_mainline,
               chain_aligner, node_sorting, utils)

importlib.reload(utils)
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
# TODO: Remove input aligner to node aligner
# TODO: Remove dot nodes
# TODO: Position chains in x better during sorting (use chain bounds instead of flat offset)
# TODO: Move node types to enum?


def run_layout(node_selection: bw_node_selection.NodeSelection,
               api: bw_api_tool.APITool):
    api.log.info('Running layout Graph')

    with sd.api.sdhistoryutils.SDHistoryUtils.UndoGroup("Undo Group"):

        old_pos = dict()
        for node in node_selection.nodes:
            old_pos[node.identifier] = (node.pos.x, node.pos.y)

        api.log.debug('Sorting Nodes...')
        already_processed = list()
        for node_chain in node_selection.node_chains:
            if node_chain.root.output_node_count != 0:
                continue
            node_sorting.run_sort(node_chain.root, already_processed)

        for node in node_selection.nodes:
            # node.add_comment(str(node.alignment_behavior))
            # node.set_position(old_pos[node.identifier][0], old_pos[node.identifier][1])
            continue
            node.set_position(node.pos.x, old_pos[node.identifier][1])
        
        api.log.debug('Aligning Nodes...')
        already_processed = list()
        roots_to_update = list()
        for node_chain in node_selection.node_chains:
            if node_chain.root.output_node_count != 0:
                continue
            aligner.run_aligner(node_chain.root, already_processed, roots_to_update, node_selection)

        #TODO: A post pass to fix overlapping roots

        # api.log.debug('Aligning by hiararchy...')
        # for node_chain in node_selection.node_chains:
        #     aligner = input_aligner.HiarachyAlign()
        #     aligner.run(node_chain.root)

        # # Position all roots starting from the top of tree
        # api.log.debug('Aligning node chains...')
        # seen = list()
        # for node_chain in node_selection.node_chains:
        #     if node_chain.root.output_node_count != 0:
        #         continue
        #     aligner = chain_aligner.ChainAligner()
        #     # aligner.run(node_chain.root, seen)

        # api.log.debug('Removing overlap...')
        # seen = list()
        # for node_chain in node_selection.node_chains:
        #     if node_chain.root.output_node_count != 0:
        #         continue
        #     aligner = input_aligner.RemoveOverlap()
        #     aligner.run2(node_chain.root, seen)

        

def on_clicked_layout_graph(api: bw_api_tool):
    node_selection = bw_node_selection.NodeSelection(api.current_selection, api.current_graph)
    run_layout(node_selection, api)


def on_graph_view_created(_, api: bw_api_tool.APITool):
    icon_path = Path(__file__).parent / 'resources/icons/bwLayoutGraphIcon.png'
    action = api.graph_view_toolbar.addAction(QtGui.QIcon(str(icon_path.resolve())), '')
    action.setToolTip('Layout Graph')
    action.triggered.connect(lambda: on_clicked_layout_graph(api))


def on_initialize(api: bw_api_tool.APITool):
    api.register_on_graph_view_created_callback(partial(on_graph_view_created, api=api))





# #TODO:
# # layout pass
# class NodeType(Enum):
#     Blend = 'sbs::compositing::blend'
#     Dot = 'sbs::compositing::passthrough'
#
#
# def onClickedLayoutButton(aSettingsFile, aUiMgr, aPkgMgr, aLogger):
#     start = time.time()
#
#     with SDHistoryUtils.UndoGroup('Move Chain Undo Group'):
#         aLogger.info(f'Running Layout Graph')
#
#         try:
#             currentGraphSelection = aUiMgr.getCurrentGraphSelection()
#             currentGraph = aUiMgr.getCurrentGraph()
#         except APIException:
#             aLogger.info(f'No graph found')
#             return
#         else:
#             if len(currentGraphSelection) == 0:
#                 aLogger.info(f'No nodes selected')
#                 return
#
#             moduleSettings = aSettingsFile.getModuleSettings(bwSettings.SupportedModules.LayoutGraph.value)
#             verbose = moduleSettings['detailedLog']
#
#             if len(currentGraphSelection) >= moduleSettings['selectionCountWarning']:
#                 ret = QtWidgets.QMessageBox.question(
#                     None,
#                     '',
#                     "Running Layout Graph on a large selection could take a while, are you sure you want to continue",
#                     QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
#
#                 if ret == QtWidgets.QMessageBox.No:
#                     return
#
#             if verbose:
#                 aLogger.info(f'Deleteing DOT nodes...')
#             _deleteAllDotNodes(aUiMgr.getCurrentGraphSelection(), aUiMgr.getCurrentGraph())
#
#             if verbose:
#                 aLogger.info(f'Gathering node chain...')
#             nodeChain = bwNodeChain.NodeChain(
#                 aUiMgr.getCurrentGraphSelection(),
#                 aUiMgr.getCurrentGraph(),
#                 moduleSettings,
#                 aLogger=aLogger)
#             if verbose:
#                 aLogger.info(f'{nodeChain}')
#
#             # if moduleSettings['advancedSettings']['hierarchyPass']:
#             if verbose:
#                 aLogger.info(f'{"-"*30}')
#                 aLogger.info(f'{"-"*30}')
#                 aLogger.info(f'Building hierarchy...')
#
#             bwLayoutPass.HierarchyPass(nodeChain)
#
#             # if moduleSettings['advancedSettings']['mainlineLanePass']:
#             if verbose:
#                 aLogger.info(f'{"-"*30}')
#                 aLogger.info(f'{"-"*30}')
#                 aLogger.info(f'Evaluating mainline...')
#             bwLayoutPass.MainlinePass(nodeChain)
#
#             # reset the mainline index as it was likely changed after the mainline shuffle
#             # we still only want to compute it once per node though
#             for node in nodeChain.nodes:
#                 node._mainlineIndex = None
#
#             # if moduleSettings['advancedSettings']['verticalPass']:
#             if verbose:
#                 aLogger.info(f'{"-"*30}')
#                 aLogger.info(f'{"-"*30}')
#                 aLogger.info(f'Arranging vertical...')
#             bwLayoutPass.VerticalPassStructure(nodeChain)
#
#             # if moduleSettings['advancedSettings']['secondVerticalPass']:
#             if verbose:
#                 aLogger.info(f'{"-"*30}')
#                 aLogger.info(f'{"-"*30}')
#                 aLogger.info(f'Resolving overlaps...')
#             bwLayoutPass.SecondVerticalPass(nodeChain)
#
#     end = time.time()
#     elapsedTime = end - start
#     aLogger.info(f'Layout ran in {elapsedTime} seconds')
#
# def addToToolBar(aSettingsFile, aUIMgr, aPkgMgr, aLogger):
#     bwToolBar = bwUtils.findBWToolBar()[0]
#     if bwToolBar:
#         layoutIconPath = f'{os.path.dirname(__file__)}\\resources\\icons\\bwLayoutGraphIcon.png'
#         action = bwToolBar.addAction(QtGui.QIcon(layoutIconPath), '')
#         # action = bwToolBar.addAction('Layout')
#         action.setObjectName('bw.layoutGraphAction')
#
#         # Hotkey
#         moduleSettings = aSettingsFile.getModuleSettings(bwSettings.SupportedModules.LayoutGraph.value)
#         action.setShortcut(QtGui.QKeySequence(moduleSettings['hotkey']))
#         action.setToolTip("Layout Graph")
#         action.triggered.connect(lambda: onClickedLayoutButton(aSettingsFile, aUIMgr, aPkgMgr, aLogger))
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
