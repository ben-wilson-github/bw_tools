import os
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

    # def tearDown(self) -> None:
    #     self.pkg_mgr.unloadUserPackage(self.package)
    #     self.package = self.pkg_mgr.loadUserPackage(self.package_file_path)

    def test_single_node(self):
        graph = self.package.findResourceFromUrl('test_single_node')
        node_selection = bw_node_selection.NodeSelection(graph.getNodes(), graph)

        bw_layout_graph.run_layout(node_selection, self.api)

        self.assertEqual(16, graph.getNodes()[0].getPosition().x)
        self.assertEqual(16, graph.getNodes()[0].getPosition().y)


    def test_line_of_nodes(self):
        graph = self.package.findResourceFromUrl('test_line_of_nodes')
        n1 = graph.getNodeFromId('1408049754')
        n2 = graph.getNodeFromId('1408083786')
        n3 = graph.getNodeFromId('1408083790')
        expected1 = [16, 16]
        expected2 = [-112, 16]
        expected3 = [-240, 16]

        bw_layout_graph.run_layout(bw_node_selection.NodeSelection([n1, n2, n3], self.api), self.api)

        self.assertEqual(expected1[0], n1.getPosition().x)
        self.assertEqual(expected1[1], n1.getPosition().y)

        self.assertEqual(expected2[0], n2.getPosition().x)
        self.assertEqual(expected2[1], n2.getPosition().y)

        self.assertEqual(expected3[0], n3.getPosition().x)
        self.assertEqual(expected3[1], n3.getPosition().y)

if __name__ == '__main__':
    unittest.main()
