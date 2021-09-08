from __future__ import annotations

import json
from functools import partial
from pathlib import Path
from typing import TYPE_CHECKING

from bw_tools.common.bw_node_selection import NodeSelection
from bw_tools.modules.bw_settings.bw_settings import ModuleSettings

from . import atomic_optimizer, comp_graph_optimizer, uniform_color_optimizer

if TYPE_CHECKING:
    from bw_tools.common.bw_api_tool import APITool

from PySide2 import QtGui, QtWidgets
from sd.api.sdhistoryutils import SDHistoryUtils

# TODO: unit tests
# TODO: Add auto layout and straighten option


class OptimizeSettings(ModuleSettings):
    def __init__(self, file_path: Path):
        super().__init__(file_path)
        self.hotkey: str = self.get("Hotkey;value")
        self.recursive: bool = self.get("Recursive;value")
        self.uniform_force_output_size: bool = self.get(
            "Uniform Color Node Settings;value;Force Output Size (16x16);value"
        )


def run(node_selection: NodeSelection, api: APITool):
    if node_selection.node_count == 0:
        return

    settings = OptimizeSettings(
        Path(__file__).parent / "bw_optimize_graph_settings.json"
    )

    atomic_count = 0
    comp_graph_count = 0
    deleted = True
    while deleted:
        deleted = False

        optimizer = atomic_optimizer.AtomicOptimizer(node_selection, settings)
        optimizer.run()
        if settings.recursive:
            while optimizer.deleted_count >= 1:
                deleted = True
                atomic_count += optimizer.deleted_count
                optimizer.run()

        optimizer = comp_graph_optimizer.CompGraphOptimizer(
            node_selection, settings
        )
        optimizer.run()
        if settings.recursive:
            while optimizer.deleted_count >= 1:
                deleted = True
                comp_graph_count += optimizer.deleted_count
                optimizer.run()

    # Handle uniform colors
    uniform_color_count = 0
    if settings.uniform_force_output_size:
        optimizer = uniform_color_optimizer.UniformOptimizer(
            node_selection, settings
        )
        optimizer.run()
        uniform_color_count = optimizer.optimized_count

    msg = (
        f"Found {uniform_color_count + atomic_count + comp_graph_count}"
        " nodes to optimize..\n"
        f"\n Uniform Color Nodes: {uniform_color_count} optimized"
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
    settings = OptimizeSettings(
        Path(__file__).parent / "bw_optimize_graph_settings.json"
    )

    icon = Path(__file__).parent / "resources/icons/bw_optimize_graph.png"
    action = api.graph_view_toolbar.addAction(
        QtGui.QIcon(str(icon.resolve())), ""
    )
    action.setShortcut(QtGui.QKeySequence(settings.hotkey))
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
