import unittest

from tests import (
    test_chain_dimension,
    test_framer,
    test_layout_graph,
    test_node,
    test_node_selection,
    test_straighten_connection,
    test_optimize_graph,
)


def run():
    print("Running test_node")
    unittest.main(module=test_node, exit=False)
    print("Running test_node_selection")
    unittest.main(module=test_node_selection, exit=False)
    print("Running test_chain_dimension")
    unittest.main(module=test_chain_dimension, exit=False)
    print("Running test_straighten_connection")
    unittest.main(module=test_straighten_connection, exit=False)
    print("Running test_layout_graph")
    unittest.main(module=test_layout_graph, exit=False)
    print("Running test_optimize_graph")
    unittest.main(module=test_optimize_graph, exit=False)
    print("Running test_framer")
    unittest.main(module=test_framer, exit=False)


run()
