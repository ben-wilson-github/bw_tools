from __future__ import annotations

import os
from functools import partial
from pathlib import Path
from typing import TYPE_CHECKING, Dict
from PySide2.QtGui import QIcon, QKeySequence

from PySide2.QtWidgets import QAction

from bw_tools.common.bw_node_selection import BWNodeSelection
from bw_tools.modules.bw_layout_graph import bw_layout_graph
from bw_tools.modules.bw_settings.bw_settings import BWModuleSettings
from PySide2 import QtWidgets
from sd.api.sdhistoryutils import SDHistoryUtils

from .atomic_optimizer import AtomicOptimizer
from .comp_graph_optimizer import CompGraphOptimizer
from .uniform_color_optimizer import UniformOptimizer

if TYPE_CHECKING:
    from bw_tools.common.bw_api_tool import BWAPITool


class BWOptimizeSettings(BWModuleSettings):
    def __init__(self, file_path: Path):
        super().__init__(file_path)
        self.hotkey: str = self.get("Hotkey;value")
        self.recursive: bool = self.get("Recursive;value")
        self.popup_on_complete: bool = self.get("Popup On Complete;value")
        self.run_layout_tools: bool = self.get("Run Layout Tools;value")
        self.uniform_force_output_size: bool = self.get(
            "Uniform Color Node Settings;content;"
            "Force Output Size (16x16);value"
        )


def run(
    node_selection: BWNodeSelection,
    api: BWAPITool,
    settings: BWOptimizeSettings,
):
    if node_selection.node_count == 0:
        return

    atomic_count = 0
    comp_graph_count = 0
    deleted = True
    while deleted:
        deleted = False

        optimizer = AtomicOptimizer(node_selection, settings)
        optimizer.run()
        if settings.recursive:
            while optimizer.deleted_count >= 1:
                deleted = True
                atomic_count += optimizer.deleted_count
                optimizer.run()

        optimizer = CompGraphOptimizer(node_selection, settings)
        optimizer.run()
        if settings.recursive:
            while optimizer.deleted_count >= 1:
                deleted = True
                comp_graph_count += optimizer.deleted_count
                optimizer.run()

    # Handle uniform colors
    uniform_color_count = 0
    if settings.uniform_force_output_size:
        optimizer = UniformOptimizer(node_selection, settings)
        optimizer.run()
        uniform_color_count = optimizer.optimized_count

    if settings.run_layout_tools:
        api_nodes = [n.api_node for n in node_selection.nodes]
        bw_layout_graph.run_layout(
            bw_layout_graph.BWLayoutNodeSelection(
                api_nodes, node_selection.api_graph
            ),
            api,
        )

    msg = (
        f"Found {uniform_color_count + atomic_count + comp_graph_count}"
        " nodes to optimize..\n"
        f"\n Uniform Color Nodes: {uniform_color_count} optimized"
        f"\nAtmoic Nodes: {atomic_count} deleted"
        f"\nComp Graph Nodes: {comp_graph_count} deleted"
    )

    api.log.info(msg)

    if settings.popup_on_complete:
        QtWidgets.QMessageBox.information(
            None, "", msg, QtWidgets.QMessageBox.Ok
        )


def _on_clicked_run(api: BWAPITool):
    if not api.current_graph_is_supported:
        api.log.error("Graph type is unsupported")
        return

    pkg = api.current_package
    file_path = Path(pkg.getFilePath())
    if not os.access(file_path, os.W_OK):
        api.log.error("Permission denied to write to package")
        return

    with SDHistoryUtils.UndoGroup("Optimize Nodes"):
        api.log.info("Running optimize graph...")
        node_selection = BWNodeSelection(
            api.current_node_selection, api.current_graph
        )

        settings = BWOptimizeSettings(
            Path(__file__).parent / "bw_optimize_graph_settings.json"
        )

        run(node_selection, api, settings)


def on_graph_view_created(graph_view_id, api: BWAPITool):
    api.add_toolbar_to_graph_view(graph_view_id)

    settings = BWOptimizeSettings(
        Path(__file__).parent / "bw_optimize_graph_settings.json"
    )
    icon = Path(__file__).parent / "resources/icons/bw_optimize_graph.png"
    tooltip = f"""
    Optimises the graph by identifying, removing duplicate nodes and
    optimising node settings for performance.

    Shortcut: {settings.hotkey}
    """
    action = QAction()
    action.setIcon(QIcon(str(icon.resolve())))
    action.setShortcut(QKeySequence(settings.hotkey))
    action.setToolTip(tooltip)
    action.triggered.connect(lambda: _on_clicked_run(api))
    api.graph_view_toolbar.add_action("bw_optimize_graph", action)


def on_initialize(api: BWAPITool):
    api.register_on_graph_view_created_callback(
        partial(on_graph_view_created, api=api)
    )


def get_default_settings() -> Dict:
    return {
        "Hotkey": {"widget": 1, "value": "Alt+B"},
        "Recursive": {"widget": 4, "value": True},
        "Run Layout Tools": {"widget": 4, "value": True},
        "Popup On Complete": {"widget": 4, "value": True},
        "Uniform Color Node Settings": {
            "widget": 0,
            "content": {
                "Force Output Size (16x16)": {"widget": 4, "value": True}
            },
        },
    }
