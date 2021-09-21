import unittest
from pathlib import Path

import sd
from bw_tools.common import bw_node, bw_node_selection


class TestNodePosition(unittest.TestCase):
    def test_x_y(self):
        print("...test_x_y")
        pos = bw_node.BWFloat2(0.0, 5.5)
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
            n = bw_node.BWNode(api_node)
            self.assertEqual(n.label, api_node.getDefinition().getLabel())

    def test_identifier_is_int(self):
        graph_name = "test_identifier_is_int"
        print(f"...{graph_name}")
        graph = self.package.findResourceFromUrl(graph_name)

        api_node = graph.getNodeFromId("1421672046")
        n = bw_node.BWNode(api_node)
        self.assertEqual(n.identifier, 1421672046)
        self.assertIsInstance(n.identifier, int)

    def test_node_height(self):
        graph_name = "test_node_height"
        print(f"...{graph_name}")
        graph = self.package.findResourceFromUrl(graph_name)

        n1 = bw_node.BWNode(graph.getNodeFromId("1421683595"))
        n2 = bw_node.BWNode(graph.getNodeFromId("1421683597"))
        n3 = bw_node.BWNode(graph.getNodeFromId("1421683600"))
        n4 = bw_node.BWNode(graph.getNodeFromId("1421683604"))
        n5 = bw_node.BWNode(graph.getNodeFromId("1421683609"))
        n6 = bw_node.BWNode(graph.getNodeFromId("1421683615"))
        nodes = [n1, n2, n3, n4, n5, n6]
        expected = [96.0, 96.0, 96.0, 117.4, 138.8, 160.2]

        for i, n in enumerate(nodes):
            self.assertEqual(n.height, expected[i])

    def test_node_width(self):
        graph_name = "test_node_width"
        print(f"...{graph_name}")
        graph = self.package.findResourceFromUrl(graph_name)

        node = bw_node.BWNode(graph.getNodes()[0])
        self.assertEqual(node.width, 96.0)

    def test_output_nodes_no_output(self):
        graph_name = "test_output_nodes_no_output"
        print(f"...{graph_name}")
        graph = self.package.findResourceFromUrl(graph_name)

        node = bw_node.BWNode(graph.getNodes()[0])
        self.assertEqual(node.output_node_count, 0)
        self.assertEqual(len(node.output_nodes), 0)

    def test_output_nodes_output_1(self):
        graph_name = "test_output_nodes_output_1"
        print(f"...{graph_name}")
        graph = self.package.findResourceFromUrl(graph_name)

        ns = bw_node_selection.BWNodeSelection(graph.getNodes(), graph)
        node = ns.node(1421698610)

        self.assertEqual(node.output_node_count, 1)
        self.assertEqual(node.output_nodes[0], ns.node(1421698928))

    def test_output_nodes_output_2(self):
        graph_name = "test_output_nodes_output_2"
        print(f"...{graph_name}")
        graph = self.package.findResourceFromUrl(graph_name)

        ns = bw_node_selection.BWNodeSelection(graph.getNodes(), graph)
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

        ns = bw_node_selection.BWNodeSelection(graph.getNodes(), graph)
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

        ns1 = bw_node_selection.BWNodeSelection(
            [input_node, output_node_1], graph
        )
        input_node = ns1.node(1421698610)
        output_node_1 = ns1.node(1421698928)

        ns2 = bw_node_selection.BWNodeSelection([output_node_2], graph)
        output_node_2 = ns2.node(1421699181)

        self.assertEqual(input_node.output_node_count, 1)
        self.assertTrue(output_node_1 in input_node.output_nodes)
        self.assertFalse(output_node_2 in input_node.output_nodes)

    def test_input_nodes_no_inputs(self):
        graph_name = "test_input_nodes_no_inputs"
        print(f"...{graph_name}")
        graph = self.package.findResourceFromUrl(graph_name)

        node = bw_node.BWNode(graph.getNodes()[0])
        self.assertEqual(node.input_node_count, 0)
        self.assertEqual(len(node.input_nodes), 0)

    def test_input_nodes_1(self):
        graph_name = "test_input_nodes_1"
        print(f"...{graph_name}")
        graph = self.package.findResourceFromUrl(graph_name)

        ns = bw_node_selection.BWNodeSelection(graph.getNodes(), graph)
        input_node = ns.node(1421698610)
        output_node = ns.node(1421698928)

        self.assertEqual(output_node.input_node_count, 1)
        self.assertTrue(input_node in output_node.input_nodes)

    def test_input_nodes_2(self):
        graph_name = "test_input_nodes_2"
        print(f"...{graph_name}")
        graph = self.package.findResourceFromUrl(graph_name)

        ns = bw_node_selection.BWNodeSelection(graph.getNodes(), graph)
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

        ns = bw_node_selection.BWNodeSelection(graph.getNodes(), graph)
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

        ns1 = bw_node_selection.BWNodeSelection(
            [input_node_1, output_node], graph
        )
        input_node_1 = ns1.node(1421698610)
        output_node = ns1.node(1421698928)
        ns2 = bw_node_selection.BWNodeSelection([input_node_2], graph)
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
        ns = bw_node_selection.BWNodeSelection(
            [api_input_node, api_output_node], graph
        )
        output_node = ns.node(1421698928)
        self.assertTrue(output_node.has_input_nodes_connected)

        ns = bw_node_selection.BWNodeSelection([api_output_node], graph)
        output_node = ns.node(1421698928)
        self.assertFalse(output_node.has_input_nodes_connected)

    def test_is_dot(self):
        graph_name = "test_is_dot"
        print(f"...{graph_name}")
        graph = self.package.findResourceFromUrl(graph_name)

        node = bw_node.BWNode(graph.getNodeFromId("1421710269"))
        dot = bw_node.BWNode(graph.getNodeFromId("1421710175"))
        self.assertFalse(node.is_dot)
        self.assertTrue(dot.is_dot)

    def test_is_root(self):
        graph_name = "test_is_root"
        print(f"...{graph_name}")
        graph = self.package.findResourceFromUrl(graph_name)

        ns = bw_node_selection.BWNodeSelection(
            [
                graph.getNodeFromId("1421710601"),
                graph.getNodeFromId("1421710269"),
            ],
            graph,
        )
        self.assertFalse(ns.node(1421710269).is_root)
        self.assertTrue(ns.node(1421710601).is_root)

    def test_has_branching_outputs(self):
        graph_name = "test_has_branching_outputs"
        print(f"...{graph_name}")
        graph = self.package.findResourceFromUrl(graph_name)

        ns = bw_node_selection.BWNodeSelection(graph.getNodes(), graph)
        self.assertTrue(ns.node(1421710269).has_branching_outputs)

        api_input_node = graph.getNodeFromId("1421710269")
        api_output_node = graph.getNodeFromId("1421710601")
        ns = bw_node_selection.BWNodeSelection(
            [api_input_node, api_output_node], graph
        )
        self.assertFalse(ns.node(1421710269).has_branching_outputs)

    def test_has_branching_inputs(self):
        graph_name = "test_has_branching_inputs"
        print(f"...{graph_name}")
        graph = self.package.findResourceFromUrl(graph_name)

        ns = bw_node_selection.BWNodeSelection(graph.getNodes(), graph)
        self.assertTrue(ns.node(1421710941).has_branching_inputs)

        api_input_node = graph.getNodeFromId("1421710601")
        api_output_node = graph.getNodeFromId("1421710941")
        ns = bw_node_selection.BWNodeSelection(
            [api_input_node, api_output_node], graph
        )
        self.assertFalse(ns.node(1421710941).has_branching_inputs)

    def test_set_position(self):
        graph_name = "test_set_position"
        print(f"...{graph_name}")
        graph = self.package.findResourceFromUrl(graph_name)

        api_node = graph.getNodes()[0]
        api_node.setPosition(sd.api.sdbasetypes.float2(100, 100))

        node = bw_node.BWNode(api_node)
        node.set_position(0, 0)

        self.assertEqual(api_node.getPosition().x, node.pos.x)
        self.assertEqual(api_node.getPosition().y, node.pos.y)


if __name__ == "__main__":
    unittest.main()
