from __future__ import annotations
from bw_tools.modules.bw_optimize_graph import uniform_color_optimizer
from bw_tools.common.bw_node_selection import NodeSelection
from bw_tools.common.bw_api_tool import SDNode

from typing import TYPE_CHECKING
from typing import List
from pathlib import Path
from functools import partial

import json, os, time
import importlib.util

from . import uniform_color_optimizer, comp_graph_optimizer, atomic_optimizer

if TYPE_CHECKING:
    from bw_tools.common.bw_api_tool import APITool

from sd.api.sdproperty import SDPropertyCategory, SDPropertyInheritanceMethod
from sd.api.apiexception import APIException
from sd.api.sdvalueint2 import SDValueInt2
from sd.api.sdvalueenum import SDValueEnum
from sd.api.sdtypeenum import SDTypeEnum
from sd.api.sdbasetypes import int2
from sd.api.sdhistoryutils import SDHistoryUtils

from PySide2 import QtGui, QtWidgets


def run(node_selection: NodeSelection, api: APITool):
    if node_selection.node_count == 0:
        return

    # Handle uniform colors
    optimizer = uniform_color_optimizer.UniformOptimizer(node_selection)
    optimizer.run()
    uniform_color_count = optimizer.deleted_count

    atomic_count = 0
    comp_graph_count = 0
    deleted = True
    while deleted:
        deleted = False

        optimizer = atomic_optimizer.AtomicOptimizer(node_selection)
        optimizer.run()
        while optimizer.deleted_count >= 1:
            deleted = True
            atomic_count += optimizer.deleted_count
            optimizer.run()

        optimizer = comp_graph_optimizer.CompGraphOptimizer(node_selection)
        optimizer.run()
        while optimizer.deleted_count >= 1:
            deleted = True
            comp_graph_count += optimizer.deleted_count
            optimizer.run()

    msg = (
        f"Found {uniform_color_count + atomic_count + comp_graph_count}"
        " nodes to optimize..\n"
        f"\n Uniform Color Nodes: {uniform_color_count} deleted or optimized"
        f"\nAtmoic Nodes: {atomic_count} deleted"
        f"\nComp Graph Nodes: {comp_graph_count} deleted"
    )

    api.log.info(msg)

    # if moduleSettings['popupOnCompletion']:
    if True:
        QtWidgets.QMessageBox.information(
            None, "", msg, QtWidgets.QMessageBox.Ok
        )


def _on_clicked_run(api: APITool):
    with SDHistoryUtils.UndoGroup("Optimize Nodes"):
        api.log.info("Running optimize graph...")
        node_selection = NodeSelection(
            api.current_selection, api.current_graph
        )
        run(node_selection, api)


def on_graph_view_created(_, api: APITool):
    # settings = StraightenSettings(
    #     Path(__file__).parent / "bw_straighten_connection_settings.json"
    # )

    icon = Path(__file__)
    action = api.graph_view_toolbar.addAction("O")
    # action.setShortcut(QtGui.QKeySequence(settings.target_hotkey))
    action.setToolTip("Optimize graph")
    action.triggered.connect(lambda: _on_clicked_run(api))


def on_initialize(api: APITool):
    api.register_on_graph_view_created_callback(
        partial(on_graph_view_created, api=api)
    )


def writeDefaultSettings(aSettingsFilePath):
    bwOptimizeGraphSettings = {}
    bwOptimizeGraphSettings["hotkey"] = "Ctrl+Alt+C"
    bwOptimizeGraphSettings["popupOnCompletion"] = True
    bwOptimizeGraphSettings["detailedLog"] = False

    uniformColorNodes = {}
    uniformColorNodes["removeDuplicates"] = True
    uniformColorNodes["outputSize"] = 16
    bwOptimizeGraphSettings["uniformColorNodes"] = uniformColorNodes

    blendNodes = {}
    blendNodes["ignoreAlpha"] = False
    bwOptimizeGraphSettings["blendNodes"] = blendNodes

    compositeNodes = {}
    compositeNodes["removeDuplicates"] = True
    compositeNodes["evaluateInputChain"] = True
    bwOptimizeGraphSettings["compositeNodes"] = compositeNodes

    with open(aSettingsFilePath) as settingsFile:
        data = json.load(settingsFile)
        data["module"][
            bwSettings.SupportedModules.OptimizeGraph.value
        ] = bwOptimizeGraphSettings

    with open(aSettingsFilePath, "w") as settingsFile:
        json.dump(data, settingsFile, indent=4)
