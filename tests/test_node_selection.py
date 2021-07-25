import os
import shutil
import unittest
import importlib

from pathlib import Path

import sd

from common import bw_node
from common import bw_node_selection
importlib.reload(bw_node)
importlib.reload(bw_node_selection)


class MyTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.package_file_path = Path(__file__).parent.joinpath(
            'resources/test_node_selection.sbs'
        )
        self.pkg_mgr = sd.getContext().getSDApplication().getPackageMgr()
        self.package = self.pkg_mgr.loadUserPackage(
            str(self.package_file_path.resolve())
        )

    def test_can_get_node(self):
        print('...test_can_get_node')
        graph = self.package.findResourceFromUrl('test_can_get_node')

        n1 = graph.getNodeFromId('1408084024')
        node_selection = bw_node_selection.NodeSelection([n1], graph)

        node_in_selection = node_selection.node('1408084024')
        self.assertEqual(1408084024, node_in_selection.identifier)
        self.assertIs(n1, node_selection.node(1408084024).api_node)

        self.assertRaises(
            bw_node_selection.NodeNotInSelectionError, node_selection.node, 1
        )

    def test_can_get_all_nodes(self):
        print('...test_can_get_all_nodes')
        graph = self.package.findResourceFromUrl('test_can_get_all_nodes')
        node_selection = bw_node_selection.NodeSelection(
            graph.getNodes(), graph
        )

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
        temp_file = Path(self.package_file_path.parent.resolve())
        temp_file = temp_file.joinpath(
            'tmp/__test_can_remove_dot_nodes.sbs'
        )
        temp_file =  str(temp_file.resolve())
        self._create_temp_file(temp_file)

        package = self.pkg_mgr.loadUserPackage(temp_file)
        graph = package.findResourceFromUrl('can_remove_dot_nodes')
        node_selection = bw_node_selection.NodeSelection(graph.getNodes(),
                                                         graph)

        node_selection.remove_dot_nodes()

        self.assertEqual(6, len(graph.getNodes()))
        node = graph.getNodeFromId('1407882793')
        expected = [0, 1, 0, 0, 0, 2, 3, 1, 1]
        properties = node.getProperties(
            sd.api.sdproperty.SDPropertyCategory.Output
        )
        for i, p in enumerate(properties):
            connections = node.getPropertyConnections(p)
            self.assertEqual(expected[i], len(connections))

        self._remove_temp_file(temp_file)

    def test_is_root_1(self):
        print('...test_is_root_1')
        graph = self.package.findResourceFromUrl('test_is_root_1')
        selection = bw_node_selection.NodeSelection(graph.getNodes(), graph)

        node = selection.node(1408093525)
        self.assertTrue(node.is_root)

    def test_is_root_2(self):
        print('...test_is_root_2')
        graph = self.package.findResourceFromUrl('test_is_root_2')
        selection = bw_node_selection.NodeSelection(graph.getNodes(), graph)

        node = selection.node(1408093545)
        self.assertTrue(node.is_root)
        node = selection.node(1408093532)
        self.assertFalse(node.is_root)

    def test_is_root_3(self):
        print('...test_is_root_3')
        graph = self.package.findResourceFromUrl('test_is_root_3')
        selection = bw_node_selection.NodeSelection(graph.getNodes(), graph)

        node = selection.node(1419304505)
        self.assertTrue(node.is_root)
        node = selection.node(1419304501)
        self.assertTrue(node.is_root)
        node = selection.node(1419304506)
        self.assertTrue(node.is_root)
        node = selection.node(1419304497)
        self.assertTrue(node.is_root)
        node = selection.node(1419304500)
        self.assertTrue(node.is_root)

    def test_is_root_4(self):
        print('...test_is_root_4')
        graph = self.package.findResourceFromUrl('test_is_root_4')
        selection = bw_node_selection.NodeSelection(graph.getNodes(), graph)

        node = selection.node(1419304502)
        self.assertTrue(node.is_root)
        node = selection.node(1419304507)
        self.assertFalse(node.is_root)
        node = selection.node(1419304498)
        self.assertTrue(node.is_root)
        node = selection.node(1419305288)
        self.assertFalse(node.is_root)

    def test_node_chain_1(self):
        print('...test_node_chain_1')
        graph = self.package.findResourceFromUrl('test_node_chain_1')
        selection = bw_node_selection.NodeSelection(graph.getNodes(), graph)
        self.assertEqual(selection.node_chain_count, 1)
        for node in graph.getNodes():
            api_identifier = int(node.getIdentifier())
            self.assertTrue(self._identifier_in_selection(api_identifier,
                                                          selection))

    def test_node_chain_2(self):
        print('...test_node_chain_2')
        graph = self.package.findResourceFromUrl('test_node_chain_2')
        selection = bw_node_selection.NodeSelection(graph.getNodes(), graph)
        self.assertEqual(selection.node_chain_count, 1)
        for node in graph.getNodes():
            api_identifier = int(node.getIdentifier())
            self.assertTrue(self._identifier_in_selection(api_identifier,
                                                          selection))

    def test_node_chain_3(self):
        print('...test_node_chain_3')
        graph = self.package.findResourceFromUrl('test_node_chain_3')
        selection = bw_node_selection.NodeSelection(graph.getNodes(), graph)
        self.assertEqual(selection.node_chain_count, 3)
        for node in graph.getNodes():
            api_identifier = int(node.getIdentifier())
            self.assertTrue(self._identifier_in_selection(api_identifier,
                                                          selection))

    def test_node_chain_4(self):
        print('...test_node_chain_4')
        graph = self.package.findResourceFromUrl('test_node_chain_4')
        selection = bw_node_selection.NodeSelection(graph.getNodes(), graph)
        self.assertEqual(selection.node_chain_count, 5)
        for node in graph.getNodes():
            api_identifier = int(node.getIdentifier())
            self.assertTrue(self._identifier_in_selection(api_identifier,
                                                          selection))

    def test_node_chain_5(self):
        print('...test_node_chain_5')
        graph = self.package.findResourceFromUrl('test_node_chain_5')
        selection = bw_node_selection.NodeSelection(graph.getNodes(), graph)
        self.assertEqual(selection.node_chain_count, 2)
        for node in graph.getNodes():
            api_identifier = int(node.getIdentifier())
            self.assertTrue(self._identifier_in_selection(api_identifier,
                                                          selection))

    def _identifier_in_selection(self,
                                 identifier: int,
                                 selection: bw_node_selection.NodeSelection):
        for node in selection.nodes:
            if identifier == node.identifier:
                return True
        return False

    def _create_temp_file(self, temp_file):
        os.makedirs(os.path.dirname(temp_file), exist_ok=True)
        shutil.copy(self.package_file_path, temp_file)

    def _remove_temp_file(self, temp_file):
        if os.path.exists(temp_file):
            os.remove(temp_file)


if __name__ == '__main__':
    unittest.main()
