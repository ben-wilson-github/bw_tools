import unittest
from pathlib import Path

from bw_tools.common.bw_node_selection import NodeSelection
from bw_tools.common import bw_chain_dimension

import sd


class TestChainDimension(unittest.TestCase):
    pkg_mgr = None
    package = None
    package_file_path = None

    @classmethod
    def setUpClass(cls) -> None:
        cls.package_file_path = (
            Path(__file__).parent / "resources" / "test_chain_dimension.sbs"
        )
        cls.pkg_mgr = sd.getContext().getSDApplication().getPackageMgr()
        cls.package = cls.pkg_mgr.loadUserPackage(
            str(cls.package_file_path.resolve())
        )

    def test_calculate_chain_dimension_throws_error_with_no_chain(self):
        graph_name = "test_calculate_chain_dimension_1_node"
        print(f"...{graph_name}")
        graph = self.package.findResourceFromUrl(graph_name)

        ns = NodeSelection(graph.getNodes(), graph)
        node = ns.nodes[0]

        self.assertRaises(
            bw_chain_dimension.BWNotInChainError,
            bw_chain_dimension.calculate_chain_dimension,
            node,
            [],
        )

    def test_calculate_chain_dimension_1_node(self):
        graph_name = "test_calculate_chain_dimension_1_node"
        print(f"...{graph_name}")
        graph = self.package.findResourceFromUrl(graph_name)

        ns = NodeSelection(graph.getNodes(), graph)
        node = ns.nodes[0]

        dimension = bw_chain_dimension.calculate_chain_dimension(
            node, ns.nodes
        )
        self.assertEqual(dimension.bounds.left, 320)
        self.assertEqual(dimension.bounds.right, 416)
        self.assertEqual(dimension.bounds.upper, 128)
        self.assertEqual(dimension.bounds.lower, 224)

        self.assertEqual(dimension.left_node, node)
        self.assertEqual(dimension.right_node, node)
        self.assertEqual(dimension.upper_node, node)
        self.assertEqual(dimension.lower_node, node)

        self.assertEqual(dimension.node_count, 1)
        self.assertEqual(dimension.width, 96)

    def test_calculate_chain_dimension_no_exclusions(self):
        graph_name = "test_calculate_chain_dimension_simple_chain"
        print(f"...{graph_name}")
        graph = self.package.findResourceFromUrl(graph_name)

        ns = NodeSelection(graph.getNodes(), graph)
        root = ns.node(1421698284)
        end = ns.node(1421712604)
        top = ns.node(1421698279)
        bot = ns.node(1421698249)

        dimension = bw_chain_dimension.calculate_chain_dimension(
            root, ns.nodes
        )
        self.assertEqual(dimension.bounds.left, 320)
        self.assertEqual(dimension.bounds.right, 864)
        self.assertEqual(dimension.bounds.upper, 0)
        self.assertEqual(dimension.bounds.lower, 352)

        self.assertEqual(dimension.left_node, end)
        self.assertEqual(dimension.right_node, root)
        self.assertEqual(dimension.upper_node, top)
        self.assertEqual(dimension.lower_node, bot)

        self.assertEqual(dimension.node_count, 4)
        self.assertEqual(dimension.width, 544)

    def test_calculate_chain_dimension_exclude_node(self):
        graph_name = "test_calculate_chain_dimension_simple_chain"
        print(f"...{graph_name}")
        graph = self.package.findResourceFromUrl(graph_name)

        ns = NodeSelection(graph.getNodes(), graph)
        root = ns.node(1421698284)
        top = ns.node(1421698279)
        bot = ns.node(1421698249)

        dimension = bw_chain_dimension.calculate_chain_dimension(
            root, [root, top, bot]
        )
        self.assertEqual(dimension.bounds.left, 480)
        self.assertEqual(dimension.bounds.right, 864)
        self.assertEqual(dimension.bounds.upper, 0)
        self.assertEqual(dimension.bounds.lower, 352)

        self.assertEqual(dimension.left_node, bot)
        self.assertEqual(dimension.right_node, root)
        self.assertEqual(dimension.upper_node, top)
        self.assertEqual(dimension.lower_node, bot)

        self.assertEqual(dimension.node_count, 3)
        self.assertEqual(dimension.width, 384)

    def test_calculate_chain_dimension_limit_bounds(self):
        graph_name = "test_calculate_chain_dimension_simple_chain"
        print(f"...{graph_name}")
        graph = self.package.findResourceFromUrl(graph_name)

        ns = NodeSelection(graph.getNodes(), graph)
        root = ns.node(1421698284)
        top = ns.node(1421698279)

        limit_bound = bw_chain_dimension.BWBound(top.pos.x)
        dimension = bw_chain_dimension.calculate_chain_dimension(
            root, ns.nodes, limit_bounds=limit_bound
        )
        self.assertEqual(dimension.bounds.left, 640)
        self.assertEqual(dimension.bounds.right, 864)
        self.assertEqual(dimension.bounds.upper, 0)
        self.assertEqual(dimension.bounds.lower, 256)

        self.assertEqual(dimension.left_node, top)
        self.assertEqual(dimension.right_node, root)
        self.assertEqual(dimension.upper_node, top)
        self.assertEqual(dimension.lower_node, root)

        self.assertEqual(dimension.node_count, 2)
        self.assertEqual(dimension.width, 224)


if __name__ == "__main__":
    unittest.main()
