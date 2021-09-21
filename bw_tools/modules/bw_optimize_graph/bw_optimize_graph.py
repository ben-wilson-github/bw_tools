from __future__ import annotations

from functools import partial
from pathlib import Path
from typing import TYPE_CHECKING, Dict

from bw_tools.common.bw_node_selection import NodeSelection
from bw_tools.modules.bw_settings.bw_settings import ModuleSettings
from bw_tools.modules.bw_layout_graph import bw_layout_graph

from . import atomic_optimizer, comp_graph_optimizer, uniform_color_optimizer

if TYPE_CHECKING:
    from bw_tools.common.bw_api_tool import BWAPITool

from PySide2 import QtGui, QtWidgets
from sd.api.sdhistoryutils import SDHistoryUtils


class OptimizeSettings(ModuleSettings):
    def __init__(self, file_path: Path):
        super().__init__(file_path)
        self.hotkey: str = self.get("Hotkey;value")
        self.recursive: bool = self.get("Recursive;value")
        self.popup_on_complete: bool = self.get("Popup On Complete;value")
        self.run_layout_tools: bool = self.get("Run Layout Tools;value")
        self.uniform_force_output_size: bool = self.get(
            "Uniform Color Node Settings;content;Force Output Size (16x16);value"
        )


def run(
    node_selection: NodeSelection, api: BWAPITool, settings: OptimizeSettings
):
    if node_selection.node_count == 0:
        return

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

    if settings.run_layout_tools:
        api_nodes = [n.api_node for n in node_selection.nodes]
        bw_layout_graph.run_layout(
            bw_layout_graph.LayoutNodeSelection(
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
    with SDHistoryUtils.UndoGroup("Optimize Nodes"):
        api.log.info("Running optimize graph...")
        node_selection = NodeSelection(
            api.current_node_selection, api.current_graph
        )

        settings = OptimizeSettings(
            Path(__file__).parent / "bw_optimize_graph_settings.json"
        )

        run(node_selection, api, settings)


def on_graph_view_created(graph_view_id, api: BWAPITool):
    toolbar = api.get_graph_view_toolbar(graph_view_id)
    if toolbar is None:
        toolbar = api.create_graph_view_toolbar(graph_view_id)

    settings = OptimizeSettings(
        Path(__file__).parent / "bw_optimize_graph_settings.json"
    )

    icon = Path(__file__).parent / "resources/icons/bw_optimize_graph.png"
    action = toolbar.addAction(QtGui.QIcon(str(icon.resolve())), "")
    action.setShortcut(QtGui.QKeySequence(settings.hotkey))
    action.setToolTip("Optimize graph")
    action.triggered.connect(lambda: _on_clicked_run(api))


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
