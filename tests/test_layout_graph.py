import importlib
import os
import random
import unittest
import shutil
import copy
from pathlib import Path
from typing import Dict

import sd
from bw_tools.common.bw_api_tool import APITool
from bw_tools.common.bw_node import Float2
from bw_tools.modules.bw_layout_graph import bw_layout_graph
from bw_tools.modules.bw_layout_graph.layout_node import (
    LayoutNode,
    LayoutNodeSelection,
)

CURRENT_DIR = Path(__file__).parent
PACKAGE_FILE_PATH = CURRENT_DIR / "resources" / "test_layouyt_graph.sbs"
TMP_FILE = CURRENT_DIR / "resources" / "tmp" / "__test_layout_graph.sbs"


class MyTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.pkg_mgr = sd.getContext().getSDApplication().getPackageMgr()
        self.package = self.pkg_mgr.getUserPackageFromFilePath(
            str(TMP_FILE.resolve())
        )
        self.api = APITool()

    def test_no_nodes_does_not_throw_error(self):
        print("...test_no_nodes_does_not_throw_error")
        graph = self.package.findResourceFromUrl(
            "test_no_nodes_does_not_throw_error"
        )
        node_selection = LayoutNodeSelection([], graph)

        bw_layout_graph.run_layout(node_selection, self.api)

        self.assertTrue(True)

    def test_single_node(self):
        print("...test_single_node")
        graph = self.package.findResourceFromUrl("test_single_node")
        node_selection = LayoutNodeSelection(graph.getNodes(), graph)

        bw_layout_graph.run_layout(node_selection, self.api)
        self.assertTrue(True)

    def test_node_chain_1(self):
        graph_name = "test_node_chain_1"
        print(f"...{graph_name}")
        self.run_layout_test_on_graph(
            self.package.findResourceFromUrl(graph_name)
        )

    def test_node_chain_2(self):
        graph_name = "test_node_chain_2"
        print(f"...{graph_name}")
        self.run_layout_test_on_graph(
            self.package.findResourceFromUrl(graph_name)
        )

    def test_node_chain_3(self):
        graph_name = "test_node_chain_3"
        print(f"...{graph_name}")
        self.run_layout_test_on_graph(
            self.package.findResourceFromUrl(graph_name)
        )


    def run_layout_test_on_graph(self, graph):
        node_selection = LayoutNodeSelection(graph.getNodes(), graph)
        original_positions = self._get_node_positions(node_selection)

        self._randomise_node_positions(node_selection)
        bw_layout_graph.run_layout(node_selection, self.api)

        new_positions = self._get_node_positions(node_selection)
        self.assertNodePositionsAreEqual(
            original_positions, new_positions, node_selection
        )

    def assertNodePositionsAreEqual(
        self,
        original_positions,
        new_positions,
        node_selection: LayoutNodeSelection,
    ):
        for node in node_selection.nodes:
            self.assertEqual(
                original_positions[node.identifier],
                new_positions[node.identifier],
            )

    def _get_node_positions(self, node_selection: LayoutNodeSelection) -> Dict:
        result = {}
        node: LayoutNode
        for node in node_selection.nodes:
            result[node.identifier] = copy.deepcopy(node.pos)
        return result

    def _randomise_node_positions(self, node_selection: LayoutNodeSelection):
        x = 300
        for node in node_selection.nodes:
            if node.is_root:
                continue
            node.set_position(
                node.pos.x + random.uniform(-x, x),
                node.pos.y + random.uniform(-x, x),
            )


if __name__ == "__main__":
    unittest.main()
