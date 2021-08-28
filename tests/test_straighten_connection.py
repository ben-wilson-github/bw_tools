from pathlib import Path
import unittest
from unittest.mock import Mock

import sd
from bw_tools.common.bw_api_tool import APITool


class TestLayoutGraphMainlineEnabledMainlineAlign(unittest.TestCase):
    packages = None
    settings = None
    pkg_mgr = None

    @classmethod
    def setUpClass(cls) -> None:
        print("...Setting up class")
        cls.packages = []

        current_dir = Path(__file__).parent
        package_file_path = (
            current_dir / "resources" / "test_straighten_connection.sbs"
        )

        s1 = Mock()
        s1.mainline_enabled = True
        s1.hotkey = "C"
        s1.node_spacing = 32.0
        s1.mainline_additional_offset = 96.0
        s1.mainline_min_threshold = 96
        s1.alignment_behavior = 0

        cls.settings = [s1]

        cls.pkg_mgr = sd.getContext().getSDApplication().getPackageMgr()
        cls.api = APITool()

    def test_straighten_connection(self):
        self.assertTrue(False)
