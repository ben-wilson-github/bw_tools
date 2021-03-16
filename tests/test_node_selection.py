import os
import unittest
import importlib

import sd

from common import bw_node_selection
importlib.reload(bw_node_selection)


class MyTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.package_file_path = os.path.join(os.path.dirname(__file__), 'resources\\test_node_selection.sbs')
        self.pkg_mgr = sd.getContext().getSDApplication().getPackageMgr()
        self.package = self.pkg_mgr.loadUserPackage(self.package_file_path)

    def tearDown(self) -> None:
        self.pkg_mgr.unloadUserPackage(self.package)
        # self.package = self.pkg_mgr.loadUserPackage(self.package_file_path)

    def test_can_delete_dot_nodes(self):
        graph = self.package.findResourceFromUrl('can_remove_dot_nodes')
        node_selection = bw_node_selection.NodeSelection(graph.getNodes(), graph)

        with sd.api.sdhistoryutils.SDHistoryUtils.UndoGroup('Test'):
            node_selection.remove_dot_nodes()

        # self.assertEqual(6, len(graph.getNodes()))
        node = graph.getNodeFromId('1407882793')
        expected = [0, 1, 0, 0, 0, 2, 3, 1, 1]
        for i, p in enumerate(node.getProperties(sd.api.sdproperty.SDPropertyCategory.Output)):
            connections = node.getPropertyConnections(p)
            self.assertEqual(expected[i], len(connections))



if __name__ == '__main__':
    unittest.main()
