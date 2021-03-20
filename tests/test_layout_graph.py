import os
import shutil
import random
import logging
import unittest
import importlib

import sd

from modules.bw_layout_graph import bw_layout_graph
from common import bw_api_tool
from common import bw_node_selection
importlib.reload(bw_api_tool)
importlib.reload(bw_layout_graph)
importlib.reload(bw_node_selection)


class MyTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.package_file_path = os.path.join(os.path.dirname(__file__), 'resources\\test_layout_graph.sbs')
        self.pkg_mgr = sd.getContext().getSDApplication().getPackageMgr()
        self.package = self.pkg_mgr.loadUserPackage(self.package_file_path)
        self.api = bw_api_tool.APITool()

    def test_layout_graphs_in_package(self):
        temp_file = os.path.join(os.path.dirname(self.package_file_path), 'tmp\\__test_layout_graph.sbs')
        self._create_temp_file(temp_file)

        temp_package = self.pkg_mgr.loadUserPackage(temp_file)
        for temp_graph in temp_package.getChildrenResources(isRecursive=False):
            temp_graph_node_selection = bw_node_selection.NodeSelection(temp_graph.getNodes(), temp_graph)
            self._randomise_node_positions(temp_graph_node_selection)
            bw_layout_graph.run_layout(temp_graph_node_selection, self.api)

        for temp_graph in temp_package.getChildrenResources(isRecursive=False):
            print(f'...{temp_graph.getIdentifier()}')
            original_graph = self.package.findResourceFromUrl(temp_graph.getIdentifier())
            original_graph_node_selection = bw_node_selection.NodeSelection(original_graph.getNodes(),
                                                                            original_graph)
            temp_graph_node_selection = bw_node_selection.NodeSelection(temp_graph.getNodes(), temp_graph)

            for temp_graph_node in temp_graph_node_selection.nodes:
                original_graph_node = original_graph_node_selection.node(temp_graph_node.identifier)

                self.assertEqual(original_graph_node.position, temp_graph_node.position)

        self._remove_temp_file(temp_file)

    def _randomise_node_positions(self, node_selection):
        for i, node in enumerate(node_selection.nodes):
            if node.is_root:
                continue
            node.set_position(node.position.x + random.uniform(-64, 64), node.position.y + random.uniform(-64, 64))

    def _create_temp_file(self, temp_file):
        os.makedirs(os.path.dirname(temp_file), exist_ok=True)
        shutil.copy(self.package_file_path, temp_file)

    def _remove_temp_file(self, temp_file):
        if os.path.exists(temp_file):
            os.remove(temp_file)

if __name__ == '__main__':
    unittest.main()
