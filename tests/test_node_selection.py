import shutil
import unittest
from pathlib import Path

import sd
from bw_tools.common import bw_node_selection


class TestNodeSelection(unittest.TestCase):
    pkg_mgr = None
    package = None
    package_file_path = None

    @classmethod
    def setUpClass(cls) -> None:
        cls.package_file_path = (
            Path(__file__).parent / "resources" / "test_node_selection.sbs"
        )
        cls.pkg_mgr = sd.getContext().getSDApplication().getPackageMgr()
        cls.package = cls.pkg_mgr.loadUserPackage(
            str(cls.package_file_path.resolve())
        )

    def test_can_get_node(self):
        print("...test_can_get_node")
        graph = self.package.findResourceFromUrl("test_can_get_node")

        n1 = graph.getNodeFromId("1408084024")
        node_selection = bw_node_selection.NodeSelection([n1], graph)

        node_in_selection = node_selection.node("1408084024")
        self.assertEqual(1408084024, node_in_selection.identifier)
        self.assertIs(n1, node_selection.node(1408084024).api_node)

    def test_node_not_in_selection_is_raised(self):
        print("...test_node_not_in_selection_is_raised")
        graph = self.package.findResourceFromUrl("test_can_get_node")
        ns = bw_node_selection.NodeSelection(graph.getNodes(), graph)

        self.assertRaises(
            bw_node_selection.NodeNotInSelectionError, ns.node, 1
        )

    def test_can_get_all_nodes(self):
        print("...test_can_get_all_nodes")
        graph = self.package.findResourceFromUrl("test_can_get_all_nodes")
        node_selection = bw_node_selection.NodeSelection(
            graph.getNodes(), graph
        )

        self.assertEqual(4, node_selection.node_count)
        result = (
            node_selection.node(1408284648),
            node_selection.node(1408284643),
            node_selection.node(1408284662),
            node_selection.node(1408284655),
        )
        self.assertTrue(result[0] in node_selection.nodes)
        self.assertTrue(result[1] in node_selection.nodes)
        self.assertTrue(result[2] in node_selection.nodes)
        self.assertTrue(result[3] in node_selection.nodes)

    def test_node_count(self):
        print("...test_node_count")
        graph = self.package.findResourceFromUrl("test_node_count")
        node_selection = bw_node_selection.NodeSelection(
            graph.getNodes(), graph
        )
        self.assertEqual(node_selection.node_count, 3)

    def test_contains(self):
        print("...test_contains")
        graph = self.package.findResourceFromUrl("test_contains")
        node_selection = bw_node_selection.NodeSelection(
            graph.getNodes(), graph
        )
        n = node_selection.node(1408284655)
        self.assertTrue(node_selection.contains(n))

        n1 = graph.getNodeFromId("1408284655")
        n2 = graph.getNodeFromId("1408284643")
        ns1 = bw_node_selection.NodeSelection([n1], graph)
        ns2 = bw_node_selection.NodeSelection([n2], graph)
        self.assertFalse(ns1.contains(ns2.node(1408284643)))

    def test_can_remove_dot_nodes(self):
        print("...test_can_remove_dot_nodes")
        temp_file = Path(self.package_file_path.parent.resolve())
        temp_file = temp_file / "tmp" / "__test_can_remove_dot_nodes.sbs"

        self._create_temp_file(temp_file)

        package = self.pkg_mgr.loadUserPackage(str(temp_file.resolve()))
        graph = package.findResourceFromUrl("can_remove_dot_nodes")

        bw_node_selection.remove_dot_nodes(graph.getNodes(), graph)
        node_selection = bw_node_selection.NodeSelection(
            graph.getNodes(), graph
        )

        self.assertTrue(all(not node.is_dot for node in node_selection.nodes))

        temp_file.unlink()

    def _create_temp_file(self, tmp_file: Path):
        if not tmp_file.parent.is_dir():
            tmp_file.parent.mkdir()
        if tmp_file.is_file():
            tmp_file.unlink()

        shutil.copy(self.package_file_path, tmp_file)


if __name__ == "__main__":
    unittest.main()
