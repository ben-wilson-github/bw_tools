import unittest
import importlib
from dataclasses import dataclass

from common import bw_node

import sd

importlib.reload(bw_node)

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
        self.package = sd.getContext().getSDApplication().getPackageMgr().newUserPackage()
        self.graph = sd.api.sbs.sdsbscompgraph.SDSBSCompGraph.sNew(self.package)

    def tearDown(self) -> None:
        # comment this to see resulting packages
        self.package = sd.getContext().getSDApplication().getPackageMgr().unloadUserPackage(self.package)
        pass

    def test_throws_type_error(self):
        with self.assertRaises(TypeError):
            bw_node.Node(1)

    def test_atomic_uniform_node(self):
        node = self.graph.newNode('sbs::compositing::uniform')
        node_results = NodeResults(
            label=node.getDefinition().getLabel(),
            has_label=True,
            identifier=node.getIdentifier(),
            position_x=node.getPosition().x,
            position_y=node.getPosition().y,
            input_slot_count=0,
            output_slot_count=1,
            inputs_connected=0,
            outputs_connected=0
        )
        node = bw_node.Node(node)
        self._test_node_properties(node, node_results)

    def test_can_get_nodes_connected_to_property(self):
        levels_node = self.graph.newNode('sbs::compositing::levels')
        sharpen_node = self.graph.newNode('sbs::compositing::sharpen')
        blur_node = self.graph.newNode('sbs::compositing::blur')
        hsl_node = self.graph.newNode('sbs::compositing::hsl')
        sharpen_node.setPosition(sd.api.sdbasetypes.float2(128, 128))
        blur_node.setPosition(sd.api.sdbasetypes.float2(128, -128))
        hsl_node.setPosition(sd.api.sdbasetypes.float2(256, 0))

        levels_node.newPropertyConnectionFromId('unique_filter_output', sharpen_node, 'input1')
        levels_node.newPropertyConnectionFromId('unique_filter_output', blur_node, 'input1')

        node = bw_node.Node(levels_node)
        for p in node.output_connectable_properties:
            self.assertEqual(2, node.get_property_connections_count(p))
            self.assertIsInstance(node.get_property_connections(p), sd.api.sdarray.SDArray)
            self.assertIsInstance(node.get_property_connections(p)[0], sd.api.sdconnection.SDConnection)

        for p in node.output_connectable_properties:
            self.assertEqual(2, node.get_property_connections_input_nodes_count(p))
            self.assertIsInstance(node.get_property_connections_input_nodes(p), tuple)
            self.assertIsInstance(node.get_property_connections_input_nodes(p)[0], bw_node.Node)

        node = bw_node.Node(hsl_node)
        p = hsl_node.getPropertyFromId(
            'unique_filter_output', sd.api.sdproperty.SDPropertyCategory.Output
        )
        self.assertEqual(tuple(), node.get_property_connections_input_nodes(p))
        self.assertEqual(0, node.get_property_connections_input_nodes_count(p))

        with self.assertRaises(TypeError):
            node.get_property_connections_input_nodes(1)
        with self.assertRaises(TypeError):
            node.get_property_connections_input_nodes_count(1)

    def test_connected_nodes(self):
        levels_node = self.graph.newNode('sbs::compositing::levels')
        sharpen_node = self.graph.newNode('sbs::compositing::sharpen')
        sharpen_node.setPosition(sd.api.sdbasetypes.float2(-128, 0))
        sharpen_node.newPropertyConnectionFromId('unique_filter_output', levels_node, 'input1')

        levels_results = NodeResults(
            label=levels_node.getDefinition().getLabel(),
            has_label=True,
            identifier=levels_node.getIdentifier(),
            position_x=levels_node.getPosition().x,
            position_y=levels_node.getPosition().y,
            input_slot_count=1,
            output_slot_count=1,
            inputs_connected=0,
            outputs_connected=1
        )
        sharpen_results = NodeResults(
            label=sharpen_node.getDefinition().getLabel(),
            has_label=True,
            identifier=sharpen_node.getIdentifier(),
            position_x=sharpen_node.getPosition().x,
            position_y=sharpen_node.getPosition().y,
            input_slot_count=1,
            output_slot_count=1,
            inputs_connected=1,
            outputs_connected=0
        )
        levels_node = bw_node.Node(levels_node)
        sharpen_node = bw_node.Node(sharpen_node)
        self._test_node_properties(levels_node, levels_results)
        self._test_node_properties(sharpen_node, sharpen_results)

    def _test_node_properties(self, node, node_results):
        # label
        self.assertEqual(node_results.label, node.label)
        self.assertEqual(node_results.has_label, node.has_label)

        # Identifier
        self.assertEqual(node_results.identifier, str(node.identifier))
        self.assertIsInstance(node.identifier, int)

        # Position
        self.assertEqual(node_results.position_x, node.position.x)
        self.assertEqual(node_results.position_y, node.position.y)

        # Width
        # Height

        # Input slots
        self.assertEqual(node_results.input_slot_count, node.input_connectable_properties_count)
        self.assertIsInstance(node.input_connectable_properties, tuple)
        for p in node.input_connectable_properties:
            self.assertIsInstance(p, sd.api.sdproperty.SDProperty)

        # Output slots
        self.assertEqual(node_results.output_slot_count, node.output_connectable_properties_count)
        self.assertIsInstance(node.output_connectable_properties, tuple)
        for p in node.output_connectable_properties:
            self.assertIsInstance(p, sd.api.sdproperty.SDProperty)


if __name__ == '__main__':
    unittest.main()
