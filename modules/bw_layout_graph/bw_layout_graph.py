import os
import importlib
from functools import partial

from PySide2 import QtWidgets
from PySide2 import QtGui

from common import bw_api_tool
from common import bw_node_selection
importlib.reload(bw_api_tool)
importlib.reload(bw_node_selection)
# import json, time, os
# import importlib.util
#
# from enum import Enum
#
# from common import (
#     bwSettings,
#     bwUtils
# )
# from modules.bw_layout_graph.lib import (
#     bwNodeChain,
#     bwLayoutPass
# )
#
# importlib.reload(bwSettings)
# importlib.reload(bwNodeChain)
# importlib.reload(bwLayoutPass)
# importlib.reload(bwUtils)
#
# from sd.ui.graphgrid import GraphGrid
# from sd.api.sdbasetypes import float2
# from sd.api.sdproperty import SDPropertyCategory
# from sd.api.sdtypetexture import SDTypeTexture
# from sd.api.sdhistoryutils import SDHistoryUtils
# from sd.api.apiexception import APIException
#
# from PySide2 import QtCore, QtGui, QtWidgets

def run_layout(node_selection: bw_node_selection.NodeSelection, api: bw_api_tool.APITool) -> None:
    api.log.info('Running layout Graph')
    node_selection.remove_dot_nodes()

    for root_node in node_selection.root_nodes:
        print(root_node)

def on_clicked_layout_graph(api: bw_api_tool) -> None:
    node_selection = bw_node_selection.NodeSelection(api.current_selection, api.current_graph)
    run_layout(node_selection, api)

def on_graph_view_created(_, api: bw_api_tool.APITool) -> None:
    icon = os.path.normpath(
        os.path.join(
            os.path.dirname(__file__),
            'resources\\icons\\bwLayoutGraphIcon.png'
        )
    )
    action = api.graph_view_toolbar.addAction(QtGui.QIcon(icon), '')
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