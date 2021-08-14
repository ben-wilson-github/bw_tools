import importlib
import shutil
import unittest
from pathlib import Path

import sd

from tests import test_layout_graph, test_node_selection

importlib.reload(test_node_selection)
importlib.reload(test_layout_graph)


def set_layout_graph():
    current_dir = Path(__file__).parent
    package_file_path = current_dir / "resources" / "test_layout_graph.sbs"
    tmp_file = current_dir / "resources" / "tmp" / "__test_layout_graph.sbs"
    if not tmp_file.is_file():
        tmp_file.touch()
    shutil.copy(package_file_path, tmp_file)

    pkg_mgr = sd.getContext().getSDApplication().getPackageMgr()
    package = pkg_mgr.loadUserPackage(str(tmp_file.resolve()))


# print('Running test_nodes')
# unittest.main(module=test_nodes, exit=False)
# unittest.main(module=text_straighten_connection, exit=True)
# print('Running test_node_selection')
# unittest.main(module=test_node_selection, exit=False)
print("Running test_layout_graph")
set_layout_graph()
unittest.main(module=test_layout_graph, exit=False)
