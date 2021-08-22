import importlib
import unittest

import sd

from tests import test_layout_graph, test_node_selection, test_node


def run():
    print("Running test_node")
    unittest.main(module=test_node, exit=False)
    print("Running test_node_selection")
    unittest.main(module=test_node_selection, exit=False)
    # unittest.main(module=text_straighten_connection, exit=True)

    # print("Running test_layout_graph")
    # unittest.main(module=test_layout_graph, exit=False)
