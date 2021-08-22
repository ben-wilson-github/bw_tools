import os
import unittest
import importlib
from dataclasses import dataclass
from pathlib import Path

from bw_tools.common import bw_node, bw_node_selection

import sd


@dataclass()
class NodeResults:
    label: str
    has_label: True
    identifier: int
    position_x: float
    position_y: float
    input_slot_count: int
    output_slot_count: int
    inputs_connected: int
    outputs_connected: int


class TestNodePosition(unittest.TestCase):
    def test_x_y(self):
        print("...test_x_y")
        pos = bw_node.Float2(0.0, 5.5)
        self.assertEqual(0.0, pos.x)
        self.assertEqual(5.5, pos.y)


class TestNode(unittest.TestCase):
    pkg_mgr = None
    package = None
    package_file_path = None

    @classmethod
    def setUpClass(cls) -> None:
        cls.package_file_path = (
            Path(__file__).parent / "resources" / "test_node.sbs"
        )
        cls.pkg_mgr = sd.getContext().getSDApplication().getPackageMgr()
        cls.package = cls.pkg_mgr.loadUserPackage(
            str(cls.package_file_path.resolve())
        )

    def test_label(self):
        graph_name = "test_label"
        print(f"...{graph_name}")
        graph = self.package.findResourceFromUrl(graph_name)

        node_with_label = graph.getNodeFromId("1421672046")
        node_without_label = graph.getNodeFromId("1421672096")

        for api_node in [node_with_label, node_without_label]:
            n = bw_node.Node(api_node)
            self.assertEqual(n.label, api_node.getDefinition().getLabel())

    def test_identifier_is_int(self):
        graph_name = "test_identifier_is_int"
        print(f"...{graph_name}")
        graph = self.package.findResourceFromUrl(graph_name)

        api_node = graph.getNodeFromId("1421672046")
        n = bw_node.Node(api_node)
        self.assertEqual(n.identifier, 1421672046)
        self.assertIsInstance(n.identifier, int)

    def test_node_height(self):
        graph_name = "test_node_height"
        print(f"...{graph_name}")
        graph = self.package.findResourceFromUrl(graph_name)

        n1 = bw_node.Node(graph.getNodeFromId("1421683595"))
        n2 = bw_node.Node(graph.getNodeFromId("1421683597"))
        n3 = bw_node.Node(graph.getNodeFromId("1421683600"))
        n4 = bw_node.Node(graph.getNodeFromId("1421683604"))
        n5 = bw_node.Node(graph.getNodeFromId("1421683609"))
        n6 = bw_node.Node(graph.getNodeFromId("1421683615"))
        nodes = [n1, n2, n3, n4, n5, n6]
        expected = [96.0, 96.0, 96.0, 117.4, 138.8, 160.2]

        for i, n in enumerate(nodes):
            self.assertEqual(n.height, expected[i])

    def test_node_width(self):
        graph_name = "test_node_width"
        print(f"...{graph_name}")
        graph = self.package.findResourceFromUrl(graph_name)

        node = bw_node.Node(graph.getNodes()[0])
        self.assertEqual(node.width, 96.0)

    def test_output_nodes_no_output(self):
        graph_name = "test_output_nodes_no_output"
        print(f"...{graph_name}")
        graph = self.package.findResourceFromUrl(graph_name)

        node = bw_node.Node(graph.getNodes()[0])
        self.assertEqual(node.output_node_count, 0)
        self.assertEqual(len(node.output_nodes), 0)

    def test_output_nodes_output_1(self):
        graph_name = "test_output_nodes_output_1"
        print(f"...{graph_name}")
        graph = self.package.findResourceFromUrl(graph_name)

        ns = bw_node_selection.NodeSelection(graph.getNodes(), graph)
        node = ns.node(1421698610)

        self.assertEqual(node.output_node_count, 1)
        self.assertEqual(node.output_nodes[0], ns.node(1421698928))

    def test_output_nodes_output_2(self):
        graph_name = "test_output_nodes_output_2"
        print(f"...{graph_name}")
        graph = self.package.findResourceFromUrl(graph_name)

        ns = bw_node_selection.NodeSelection(graph.getNodes(), graph)
        input_node = ns.node(1421698610)
        output_node_1 = ns.node(1421698928)
        output_node_2 = ns.node(1421699181)

        self.assertEqual(input_node.output_node_count, 2)
        self.assertTrue(output_node_1 in input_node.output_nodes)
        self.assertTrue(output_node_2 in input_node.output_nodes)

    def test_output_nodes_multiple_connections(self):
        graph_name = "test_output_nodes_multiple_connections"
        print(f"...{graph_name}")
        graph = self.package.findResourceFromUrl(graph_name)

        ns = bw_node_selection.NodeSelection(graph.getNodes(), graph)
        input_node = ns.node(1421698610)
        output_node_1 = ns.node(1421698928)
        output_node_2 = ns.node(1421699181)

        self.assertEqual(input_node.output_node_count, 2)
        self.assertTrue(output_node_1 in input_node.output_nodes)
        self.assertTrue(output_node_2 in input_node.output_nodes)

    def test_output_nodes_output_not_in_selection(self):
        graph_name = "test_output_nodes_output_not_in_selection"
        print(f"...{graph_name}")
        graph = self.package.findResourceFromUrl(graph_name)

        input_node = graph.getNodeFromId("1421698610")
        output_node_1 = graph.getNodeFromId("1421698928")
        output_node_2 = graph.getNodeFromId("1421699181")

        ns1 = bw_node_selection.NodeSelection(
            [input_node, output_node_1], graph
        )
        input_node = ns1.node(1421698610)
        output_node_1 = ns1.node(1421698928)

        ns2 = bw_node_selection.NodeSelection([output_node_2], graph)
        output_node_2 = ns2.node(1421699181)

        self.assertEqual(input_node.output_node_count, 1)
        self.assertTrue(output_node_1 in input_node.output_nodes)
        self.assertFalse(output_node_2 in input_node.output_nodes)

    def test_input_nodes_no_inputs(self):
        graph_name = "test_input_nodes_no_inputs"
        print(f"...{graph_name}")
        graph = self.package.findResourceFromUrl(graph_name)

        node = bw_node.Node(graph.getNodes()[0])
        self.assertEqual(node.input_node_count, 0)
        self.assertEqual(len(node.input_nodes), 0)

    def test_input_nodes_1(self):
        graph_name = "test_input_nodes_1"
        print(f"...{graph_name}")
        graph = self.package.findResourceFromUrl(graph_name)

        ns = bw_node_selection.NodeSelection(graph.getNodes(), graph)
        input_node = ns.node(1421698610)
        output_node = ns.node(1421698928)

        self.assertEqual(output_node.input_node_count, 1)
        self.assertTrue(input_node in output_node.input_nodes)

    def test_input_nodes_2(self):
        graph_name = "test_input_nodes_2"
        print(f"...{graph_name}")
        graph = self.package.findResourceFromUrl(graph_name)

        ns = bw_node_selection.NodeSelection(graph.getNodes(), graph)
        input_node_1 = ns.node(1421698610)
        input_node_2 = ns.node(1421699181)
        output_node = ns.node(1421698928)

        self.assertEqual(output_node.input_node_count, 2)
        self.assertTrue(input_node_1 in output_node.input_nodes)
        self.assertTrue(input_node_2 in output_node.input_nodes)

    def test_input_nodes_multiple_connections(self):
        graph_name = "test_input_nodes_multiple_connections"
        print(f"...{graph_name}")
        graph = self.package.findResourceFromUrl(graph_name)

        ns = bw_node_selection.NodeSelection(graph.getNodes(), graph)
        input_node_1 = ns.node(1421698610)
        input_node_2 = ns.node(1421699181)
        output_node = ns.node(1421698928)

        self.assertEqual(output_node.input_node_count, 2)
        self.assertTrue(input_node_1 in output_node.input_nodes)
        self.assertTrue(input_node_2 in output_node.input_nodes)

    def test_input_nodes_input_not_in_selection(self):
        graph_name = "test_input_nodes_input_not_in_selection"
        print(f"...{graph_name}")
        graph = self.package.findResourceFromUrl(graph_name)

        input_node_1 = graph.getNodeFromId("1421698610")
        input_node_2 = graph.getNodeFromId("1421699181")
        output_node = graph.getNodeFromId("1421698928")

        ns1 = bw_node_selection.NodeSelection(
            [input_node_1, output_node], graph
        )
        input_node_1 = ns1.node(1421698610)
        output_node = ns1.node(1421698928)
        ns2 = bw_node_selection.NodeSelection([input_node_2], graph)
        input_node_2 = ns2.node(1421699181)

        self.assertEqual(output_node.input_node_count, 1)
        self.assertTrue(input_node_1 in output_node.input_nodes)
        self.assertFalse(input_node_2 in output_node.input_nodes)

    def test_input_nodes_has_input_nodes_connected(self):
        graph_name = "test_input_nodes_has_input_nodes_connected"
        print(f"...{graph_name}")
        graph = self.package.findResourceFromUrl(graph_name)

        api_input_node = graph.getNodeFromId("1421698610")
        api_output_node = graph.getNodeFromId("1421698928")
        ns = bw_node_selection.NodeSelection(
            [api_input_node, api_output_node], graph
        )
        output_node = ns.node(1421698928)
        self.assertTrue(output_node.has_input_nodes_connected)

        ns = bw_node_selection.NodeSelection([api_output_node], graph)
        output_node = ns.node(1421698928)
        self.assertFalse(output_node.has_input_nodes_connected)


#     def test_atomic_uniform_node(self):
#         graph = self.test_package.findResourceFromUrl("test_node_properties")
#         node_selection = bw_node_selection.NodeSelection(
#             graph.getNodes(), graph
#         )
#         node = node_selection.node(1408227612)

#         # label
#         self.assertEqual("Uniform Color", node.label)
#         self.assertTrue(node.has_label)

#         # Identifier
#         self.assertEqual("1408227612", str(node.identifier))
#         self.assertIsInstance(node.identifier, int)

#         # Position
#         self.assertEqual(-80, node.pos.x)
#         self.assertEqual(-48, node.pos.y)

#         # Width
#         # Height

#     def test_input_nodes(self):
#         graph = self.test_package.findResourceFromUrl("test_input_nodes")
#         node_selection = bw_node_selection.NodeSelection(
#             graph.getNodes(), graph
#         )

#         node = node_selection.node(1408223740)
#         self.assertEqual(0, node.input_node_count)
#         self.assertEqual((), node.input_nodes)
#         self.assertIsNone(node.input_node_in_index(0))

#         node = node_selection.node(1408230178)
#         result = (node_selection.node(1408223752),)
#         self.assertEqual(1, node.input_node_count)
#         self.assertEqual(result, node.input_nodes)
#         self.assertEqual(result[0], node.input_node_in_index(0))

#         node = node_selection.node(1408223766)
#         result = (
#             node_selection.node(1408223772),
#             node_selection.node(1408223782),
#             node_selection.node(1408223877),
#         )
#         self.assertEqual(3, node.input_node_count)
#         self.assertEqual(result, node.input_nodes)
#         self.assertEqual(result[0], node.input_node_in_index(0))
#         self.assertEqual(result[1], node.input_node_in_index(1))
#         self.assertEqual(result[2], node.input_node_in_index(2))

#         node = node_selection.node(1408223917)
#         result = (
#             None,
#             node_selection.node(1408223970),
#             node_selection.node(1408223970),
#             None,
#             None,
#             node_selection.node(1408223970),
#             node_selection.node(1408223970),
#             None,
#             None,
#             None,
#         )
#         self.assertEqual(1, node.input_node_count)
#         self.assertEqual((node_selection.node(1408223970),), node.input_nodes)
#         for i in range(len(result)):
#             self.assertEqual(result[i], node.input_node_in_index(i))

#         node_selection = bw_node_selection.NodeSelection(
#             [
#                 graph.getNodeFromId("1408224069"),
#                 graph.getNodeFromId("1408224068"),
#                 graph.getNodeFromId("1408230210"),
#             ],
#             graph,
#         )
#         node = node_selection.node(1408230210)
#         self.assertEqual(node.input_node_count, 2)
#         self.assertEqual(
#             node.input_nodes,
#             (node_selection.node(1408224069), node_selection.node(1408224068)),
#         )
#         self.assertEqual(
#             node_selection.node(1408224069), node.input_node_in_index(0)
#         )
#         self.assertEqual(
#             node_selection.node(1408224068), node.input_node_in_index(1)
#         )
#         self.assertIsNone(node.input_node_in_index(2))

#     def test_output_nodes(self):
#         graph = self.test_package.findResourceFromUrl("test_output_nodes")

#         node_selection = bw_node_selection.NodeSelection(
#             graph.getNodes(), graph
#         )

#         node = node_selection.node(1407968709)
#         self.assertEqual(0, node.output_node_count)
#         self.assertEqual((), node.output_nodes)

#         node = node_selection.node(1408229620)
#         self.assertEqual(1, node.output_node_count)
#         self.assertEqual((node_selection.node(1407968625),), node.output_nodes)
#         self.assertEqual(1, node.output_node_count_in_index(0))
#         self.assertEqual(
#             (node_selection.node(1407968625),), node.output_nodes_in_index(0)
#         )

#         node = node_selection.node(1408121486)
#         self.assertEqual(2, node.output_node_count)
#         self.assertEqual(
#             (
#                 node_selection.node(1408112819),
#                 node_selection.node(1408112837),
#             ),
#             node.output_nodes,
#         )
#         self.assertEqual((), node.output_nodes_in_index(0))
#         self.assertEqual(
#             (node_selection.node(1408112819),), node.output_nodes_in_index(1)
#         )
#         self.assertEqual(
#             (node_selection.node(1408112819),), node.output_nodes_in_index(2)
#         )
#         self.assertEqual((), node.output_nodes_in_index(3))
#         self.assertEqual((), node.output_nodes_in_index(4))
#         self.assertEqual((), node.output_nodes_in_index(5))
#         self.assertEqual(
#             (node_selection.node(1408112837),), node.output_nodes_in_index(6)
#         )
#         self.assertEqual((), node.output_nodes_in_index(7))
#         self.assertEqual(
#             (node_selection.node(1408112819),), node.output_nodes_in_index(8)
#         )

#         # Test only return nodes in selection
#         node_selection = bw_node_selection.NodeSelection(
#             [
#                 graph.getNodeFromId("1408230085"),
#                 graph.getNodeFromId("1407968718"),
#                 graph.getNodeFromId("1407968725"),
#             ],
#             graph,
#         )
#         node = node_selection.node(1408230085)
#         self.assertEqual(2, node.output_node_count)
#         self.assertEqual(
#             (
#                 node_selection.node(1407968718),
#                 node_selection.node(1407968725),
#             ),
#             node.output_nodes,
#         )

#     def test_center_index(self):
#         graph = self.test_package.findResourceFromUrl("test_center_index")
#         node_selection = bw_node_selection.NodeSelection(
#             graph.getNodes(), graph
#         )

#         self.assertEqual(0, node_selection.node(1408291940).center_input_index)
#         self.assertEqual(
#             0.5, node_selection.node(1408291961).center_input_index
#         )
#         self.assertEqual(1, node_selection.node(1408291946).center_input_index)
#         self.assertEqual(
#             1.5, node_selection.node(1408291971).center_input_index
#         )
#         self.assertEqual(2, node_selection.node(1408291992).center_input_index)

#     def test_node_connects_to_center(self):
#         graph = self.test_package.findResourceFromUrl(
#             "test_node_connects_to_center"
#         )
#         ns = bw_node_selection.NodeSelection(graph.getNodes(), graph)

#         self.assertFalse(
#             ns.node(1408299540).connects_to_center(ns.node(1408299544))
#         )
#         self.assertTrue(
#             ns.node(1408299553).connects_to_center(ns.node(1408299552))
#         )
#         self.assertFalse(
#             ns.node(1408299563).connects_to_center(ns.node(1408299562))
#         )
#         self.assertTrue(
#             ns.node(1408299575).connects_to_center(ns.node(1408299574))
#         )
#         self.assertTrue(
#             ns.node(1408299584).connects_to_center(ns.node(1408299585))
#         )
#         self.assertTrue(
#             ns.node(1408299594).connects_to_center(ns.node(1408299595))
#         )

#         self.assertTrue(
#             ns.node(1408299540).connects_above_center(ns.node(1408299544))
#         )
#         self.assertFalse(
#             ns.node(1408299553).connects_above_center(ns.node(1408299552))
#         )
#         self.assertFalse(
#             ns.node(1408299563).connects_above_center(ns.node(1408299562))
#         )
#         self.assertFalse(
#             ns.node(1408299575).connects_above_center(ns.node(1408299574))
#         )
#         self.assertTrue(
#             ns.node(1408299584).connects_above_center(ns.node(1408299585))
#         )
#         self.assertTrue(
#             ns.node(1408299594).connects_above_center(ns.node(1408299595))
#         )

#         self.assertFalse(
#             ns.node(1408299540).connects_below_center(ns.node(1408299544))
#         )
#         self.assertFalse(
#             ns.node(1408299553).connects_below_center(ns.node(1408299552))
#         )
#         self.assertTrue(
#             ns.node(1408299563).connects_below_center(ns.node(1408299562))
#         )
#         self.assertTrue(
#             ns.node(1408299575).connects_below_center(ns.node(1408299574))
#         )
#         self.assertFalse(
#             ns.node(1408299584).connects_below_center(ns.node(1408299585))
#         )
#         self.assertTrue(
#             ns.node(1408299594).connects_below_center(ns.node(1408299595))
#         )


if __name__ == "__main__":
    unittest.main()
