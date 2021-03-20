import os
import unittest
import importlib
from dataclasses import dataclass

from common import bw_node
from common import bw_node_selection

import sd

importlib.reload(bw_node)
importlib.reload(bw_node_selection)

# =========================================
# Tests should be run from within designer
# =========================================


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
    def test_throws_type_error(self):
        with self.assertRaises(TypeError):
            bw_node.NodePosition(1, 1)

        pos = bw_node.NodePosition(0.0, 5.5)
        self.assertEqual(0.0, pos.x)
        self.assertEqual(5.5, pos.y)


class TestNode(unittest.TestCase):
    def setUp(self) -> None:
        self.test_package_file_path = os.path.join(os.path.dirname(__file__), 'resources\\test_node.sbs')
        self.pkg_mgr = sd.getContext().getSDApplication().getPackageMgr()
        self.test_package = self.pkg_mgr.loadUserPackage(self.test_package_file_path)

    def test_atomic_uniform_node(self):
        print('...test_node_properties')
        graph = self.test_package.findResourceFromUrl('test_node_properties')
        node_selection = bw_node_selection.NodeSelection(graph.getNodes(), graph)
        node = node_selection.node(1408227612)

        # label
        self.assertEqual('Uniform Color', node.label)
        self.assertTrue(node.has_label)

        # Identifier
        self.assertEqual('1408227612', str(node.identifier))
        self.assertIsInstance(node.identifier, int)

        # Position
        self.assertEqual(-80, node.position.x)
        self.assertEqual(-48, node.position.y)

        # Width
        # Height

    def test_input_nodes(self):
        print('...test_input_nodes')
        graph = self.test_package.findResourceFromUrl('test_input_nodes')
        node_selection = bw_node_selection.NodeSelection(graph.getNodes(), graph)

        node = node_selection.node(1408223740)
        print(f'......testing {node.label}')
        self.assertEqual(0, node.input_node_count)
        self.assertEqual((), node.input_nodes)
        self.assertIsNone(node.input_node_in_index(0))

        node = node_selection.node(1408230178)
        print(f'......testing {node.label}')
        result = (node_selection.node(1408223752), )
        self.assertEqual(1, node.input_node_count)
        self.assertEqual(result, node.input_nodes)
        self.assertEqual(result[0], node.input_node_in_index(0))

        node = node_selection.node(1408223766)
        print(f'......testing {node.label}')
        result = (
            node_selection.node(1408223772),
            node_selection.node(1408223782),
            node_selection.node(1408223877),
        )
        self.assertEqual(3, node.input_node_count)
        self.assertEqual(result, node.input_nodes)
        self.assertEqual(result[0], node.input_node_in_index(0))
        self.assertEqual(result[1], node.input_node_in_index(1))
        self.assertEqual(result[2], node.input_node_in_index(2))

        node = node_selection.node(1408223917)
        print(f'......testing {node.label}')
        result = (
            None,
            node_selection.node(1408223970),
            node_selection.node(1408223970),
            None,
            None,
            node_selection.node(1408223970),
            node_selection.node(1408223970),
            None,
            None,
            None
        )
        self.assertEqual(1, node.input_node_count)
        self.assertEqual((node_selection.node(1408223970), ), node.input_nodes)
        for i in range(len(result)):
            self.assertEqual(result[i], node.input_node_in_index(i))

        node_selection = bw_node_selection.NodeSelection(
            [
                graph.getNodeFromId('1408224069'),
                graph.getNodeFromId('1408224068'),
                graph.getNodeFromId('1408230210'),
            ],
            graph
        )
        node = node_selection.node(1408230210)
        print(f'......testing {node.label}')
        self.assertEqual(node.input_node_count, 2)
        self.assertEqual(node.input_nodes, (
            node_selection.node(1408224069),
            node_selection.node(1408224068)
        ))
        self.assertEqual(node_selection.node(1408224069), node.input_node_in_index(0))
        self.assertEqual(node_selection.node(1408224068), node.input_node_in_index(1))
        self.assertIsNone(node.input_node_in_index(2))

    def test_output_nodes(self):
        print('...test_output_nodes')
        graph = self.test_package.findResourceFromUrl('test_output_nodes')

        node_selection = bw_node_selection.NodeSelection(graph.getNodes(), graph)

        node = node_selection.node(1407968709)
        print(f'......testing {node.label}')
        self.assertEqual(0, node.output_node_count)
        self.assertEqual((), node.output_nodes)

        node = node_selection.node(1408229620)
        print(f'......testing {node.label}')
        self.assertEqual(1, node.output_node_count)
        self.assertEqual((node_selection.node(1407968625), ), node.output_nodes)
        self.assertEqual(1, node.output_node_count_in_index(0))
        self.assertEqual((node_selection.node(1407968625), ), node.output_nodes_in_index(0))

        node = node_selection.node(1408121486)
        print(f'......testing {node.label}')
        self.assertEqual(2, node.output_node_count)
        self.assertEqual((
            node_selection.node(1408112819),
            node_selection.node(1408112837)
        , ), node.output_nodes)
        self.assertEqual((), node.output_nodes_in_index(0))
        self.assertEqual((node_selection.node(1408112819), ), node.output_nodes_in_index(1))
        self.assertEqual((node_selection.node(1408112819), ), node.output_nodes_in_index(2))
        self.assertEqual((), node.output_nodes_in_index(3))
        self.assertEqual((), node.output_nodes_in_index(4))
        self.assertEqual((), node.output_nodes_in_index(5))
        self.assertEqual((node_selection.node(1408112837), ), node.output_nodes_in_index(6))
        self.assertEqual((), node.output_nodes_in_index(7))
        self.assertEqual((node_selection.node(1408112819), ), node.output_nodes_in_index(8))

        # Test only return nodes in selection
        node_selection = bw_node_selection.NodeSelection(
            [
                graph.getNodeFromId('1408230085'),
                graph.getNodeFromId('1407968718'),
                graph.getNodeFromId('1407968725')
            ],
            graph
        )
        node = node_selection.node(1408230085)
        print(f'......testing {node.label}')
        self.assertEqual(2, node.output_node_count)
        self.assertEqual((
            node_selection.node(1407968718),
            node_selection.node(1407968725),
        ), node.output_nodes)

    def test_center_index(self):
        print('...test_center_index')
        graph = self.test_package.findResourceFromUrl('test_center_index')
        node_selection = bw_node_selection.NodeSelection(graph.getNodes(), graph)

        self.assertEqual(0, node_selection.node(1408291940).center_input_index)
        self.assertEqual(0.5, node_selection.node(1408291961).center_input_index)
        self.assertEqual(1, node_selection.node(1408291946).center_input_index)
        self.assertEqual(1.5, node_selection.node(1408291971).center_input_index)
        self.assertEqual(2, node_selection.node(1408291992).center_input_index)

    def test_node_connects_to_center(self):
        print('...test_node_connects_to_center')
        graph = self.test_package.findResourceFromUrl('test_node_connects_to_center')
        ns = bw_node_selection.NodeSelection(graph.getNodes(), graph)

        self.assertFalse(ns.node(1408299540).connects_to_center(ns.node(1408299544)))
        self.assertTrue(ns.node(1408299553).connects_to_center(ns.node(1408299552)))
        self.assertFalse(ns.node(1408299563).connects_to_center(ns.node(1408299562)))
        self.assertTrue(ns.node(1408299575).connects_to_center(ns.node(1408299574)))
        self.assertTrue(ns.node(1408299584).connects_to_center(ns.node(1408299585)))
        self.assertTrue(ns.node(1408299594).connects_to_center(ns.node(1408299595)))

        self.assertTrue(ns.node(1408299540).connects_above_center(ns.node(1408299544)))
        self.assertFalse(ns.node(1408299553).connects_above_center(ns.node(1408299552)))
        self.assertFalse(ns.node(1408299563).connects_above_center(ns.node(1408299562)))
        self.assertFalse(ns.node(1408299575).connects_above_center(ns.node(1408299574)))
        self.assertTrue(ns.node(1408299584).connects_above_center(ns.node(1408299585)))
        self.assertTrue(ns.node(1408299594).connects_above_center(ns.node(1408299595)))

        self.assertFalse(ns.node(1408299540).connects_below_center(ns.node(1408299544)))
        self.assertFalse(ns.node(1408299553).connects_below_center(ns.node(1408299552)))
        self.assertTrue(ns.node(1408299563).connects_below_center(ns.node(1408299562)))
        self.assertTrue(ns.node(1408299575).connects_below_center(ns.node(1408299574)))
        self.assertFalse(ns.node(1408299584).connects_below_center(ns.node(1408299585)))
        self.assertTrue(ns.node(1408299594).connects_below_center(ns.node(1408299595)))


if __name__ == '__main__':
    unittest.main()
