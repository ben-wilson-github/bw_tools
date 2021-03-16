import unittest
import importlib

from common import bw_node

import sd

importlib.reload(bw_node)

class TestStraightenConnection(unittest.TestCase):
    def setUp(self) -> None:
        self.package = sd.getContext().getSDApplication().getPackageMgr().newUserPackage()
        self.graph = sd.api.sbs.sdsbscompgraph.SDSBSCompGraph.sNew(self.package)