import importlib
import unittest

import sd

from tests import test_layout_graph, test_node_selection

importlib.reload(test_node_selection)
importlib.reload(test_layout_graph)


def run():
    # print('Running test_nodes')
    # unittest.main(module=test_nodes, exit=False)
    # unittest.main(module=text_straighten_connection, exit=True)
    # print('Running test_node_selection')
    # unittest.main(module=test_node_selection, exit=False)
    print("Running test_layout_graph")
    unittest.main(module=test_layout_graph, exit=False)
