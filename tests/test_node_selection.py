import os
import shutil
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

    def test_can_get_node(self):
        print('...test_can_get_node')
        graph = self.package.findResourceFromUrl('test_can_get_node')
        api_node = graph.getNodeFromId('1408084024')
        node_selection = bw_node_selection.NodeSelection([api_node], graph)

        self.assertEqual(1408084024, node_selection.node('1408084024').identifier)
        self.assertIs(api_node, node_selection.node(1408084024).api_node)
        self.assertIs(node_selection._node_map[1408084024], node_selection.node(1408084024))

        self.assertIsNone(node_selection.node(1))

    def test_can_get_all_nodes(self):
        print('...test_can_get_all_nodes')
        graph = self.package.findResourceFromUrl('test_can_get_all_nodes')
        node_selection =  bw_node_selection.NodeSelection(graph.getNodes(), graph)

        self.assertEqual(4, node_selection.node_count)
        result = (
            node_selection.node(1408284648),
            node_selection.node(1408284643),
            node_selection.node(1408284662),
            node_selection.node(1408284655)
        )
        self.assertTrue(result[0] in node_selection.nodes)
        self.assertTrue(result[1] in node_selection.nodes)
        self.assertTrue(result[2] in node_selection.nodes)
        self.assertTrue(result[3] in node_selection.nodes)

    def test_can_remove_dot_nodes(self):
        print('...test_can_remove_dot_nodes')
        temp_file = os.path.join(os.path.dirname(self.package_file_path), 'tmp\\__test_can_remove_dot_nodes.sbs')
        self._create_temp_file(temp_file)

        package = self.pkg_mgr.loadUserPackage(temp_file)
        graph = package.findResourceFromUrl('can_remove_dot_nodes')
        node_selection = bw_node_selection.NodeSelection(graph.getNodes(), graph)

        node_selection.remove_dot_nodes()

        self.assertEqual(6, len(graph.getNodes()))
        node = graph.getNodeFromId('1407882793')
        expected = [0, 1, 0, 0, 0, 2, 3, 1, 1]
        for i, p in enumerate(node.getProperties(sd.api.sdproperty.SDPropertyCategory.Output)):
            connections = node.getPropertyConnections(p)
            self.assertEqual(expected[i], len(connections))

        self._remove_temp_file(temp_file)

    def test_is_root(self):
        print('...test_is_root')
        graph = self.package.findResourceFromUrl('test_is_root')
        n1 = graph.getNodeFromId('1408093525')
        n2 = graph.getNodeFromId('1408093532')
        n3 = graph.getNodeFromId('1408093545')
        n4 = graph.getNodeFromId('1408093556')
        node_selection = bw_node_selection.NodeSelection([n1, n2, n3, n4], graph)

        self.assertTrue(node_selection.node(1408093525).is_root)
        self.assertFalse(node_selection.node(1408093532).is_root)
        self.assertTrue(node_selection.node(1408093545).is_root)
        self.assertTrue(node_selection.node(1408093556).is_root)

    def _create_temp_file(self, temp_file):
        os.makedirs(os.path.dirname(temp_file), exist_ok=True)
        shutil.copy(self.package_file_path, temp_file)

    def _remove_temp_file(self, temp_file):
        if os.path.exists(temp_file):
            os.remove(temp_file)


if __name__ == '__main__':
    unittest.main()
