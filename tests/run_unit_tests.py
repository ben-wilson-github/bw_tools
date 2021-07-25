import importlib
import unittest
from tests import test_nodes
from tests import test_node_selection

importlib.reload(test_nodes)
importlib.reload(test_node_selection)


#print('Running test_nodes')
#unittest.main(module=test_nodes, exit=False)
#unittest.main(module=text_straighten_connection, exit=True)
print('Running test_node_selection')
unittest.main(module=test_node_selection, exit=False)