import os
import unittest
import importlib

import sd

from common import bw_node
from common import bw_node_selection
importlib.reload(bw_node)
importlib.reload(bw_node_selection)


class MyTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.package_file_path = os.path.join(os.path.dirname(__file__), 'resources\\test_node_selection.sbs')
        self.pkg_mgr = sd.getContext().getSDApplication().getPackageMgr()
        self.package = self.pkg_mgr.loadUserPackage(self.package_file_path)

    # def tearDown(self) -> None:
    #     self.pkg_mgr.unloadUserPackage(self.package)
        # self.package = self.pkg_mgr.loadUserPackage(self.package_file_path)

    def test_can_get_node(self):
        print('...test_can_get_node')
        graph = self.package.findResourceFromUrl('test_can_get_node')
        api_node = graph.getNodeFromId('1408084024')
        node_selection = bw_node_selection.NodeSelection([api_node], graph)

        self.assertEqual(1408084024, node_selection.node('1408084024').identifier)
        self.assertIs(api_node, node_selection.node(1408084024).api_node)
        self.assertIs(node_selection._node_map[1408084024], node_selection.node(1408084024))

        self.assertIsNone(node_selection.node(1))

    def test_can_remove_dot_nodes(self):
        print('...test_can_remove_dot_nodes')
        graph = self.package.findResourceFromUrl('can_remove_dot_nodes')
        node_selection = bw_node_selection.NodeSelection(graph.getNodes(), graph)

        with sd.api.sdhistoryutils.SDHistoryUtils.UndoGroup('Test'):
            node_selection.remove_dot_nodes()

        self.assertEqual(6, len(graph.getNodes()))
        node = graph.getNodeFromId('1407882793')
        expected = [0, 1, 0, 0, 0, 2, 3, 1, 1]
        for i, p in enumerate(node.getProperties(sd.api.sdproperty.SDPropertyCategory.Output)):
            connections = node.getPropertyConnections(p)
            self.assertEqual(expected[i], len(connections))

    def test_is_root(self):
        print('...test_is_root')
        graph = self.package.findResourceFromUrl('test_is_root')
        n1 = graph.getNodeFromId('1408093525')
        n2 = graph.getNodeFromId('1408093532')
        n3 = graph.getNodeFromId('1408093545')
        n4 = graph.getNodeFromId('1408093556')
        node_selection = bw_node_selection.NodeSelection([n1, n2, n3, n4], graph)

        self.assertTrue(node_selection.node(1408093525).is_root())
        self.assertFalse(node_selection.node(1408093532).is_root())
        self.assertTrue(node_selection.node(1408093545).is_root())
        self.assertTrue(node_selection.node(1408093556).is_root())


if __name__ == '__main__':
    unittest.main()
