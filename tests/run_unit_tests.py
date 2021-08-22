import unittest

from tests import (
    test_chain_dimension,
    test_layout_graph,
    test_node,
    test_node_selection,
)


def run():
    print("Running test_node")
    unittest.main(module=test_node, exit=False)
    print("Running test_node_selection")
    unittest.main(module=test_node_selection, exit=False)
    print("Running test_chain_dimension")
    unittest.main(module=test_chain_dimension, exit=False)

    # unittest.main(module=text_straighten_connection, exit=True)

    # print("Running test_layout_graph")
    # unittest.main(module=test_layout_graph, exit=False)
