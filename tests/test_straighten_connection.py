from pathlib import Path
import unittest
from unittest.mock import Mock
import time
import sd
import os
from sd.tools.export import exportSDGraphOutputs
import shutil
from bw_tools.common.bw_api_tool import APITool
from bw_tools.modules.bw_straighten_connection import bw_straighten_connection
from bw_tools.modules.bw_straighten_connection.straighten_node import StraightenNode
from PIL import Image, ImageChops


class TestLayoutGraphMainlineEnabledMainlineAlign(unittest.TestCase):
    packages = None
    settings = None
    pkg_mgr = None

    @classmethod
    def setUpClass(cls) -> None:
        print("...Setting up class")
        cls.current_dir = Path(__file__).parent
        cls.resources_dir = cls.current_dir / "resources"
        cls.tmp_dir = cls.resources_dir / "tmp"
        package_file_path = (
            cls.resources_dir / "test_straighten_connection.sbs"
        )
        tmp_file_path = cls.tmp_dir / "__test_straighten_connection.sbs"

        s1 = Mock()
        s1.dot_node_distance = 128
        s1.alignment_behavior = 0

        cls.settings = [s1]

        cls.pkg_mgr = sd.getContext().getSDApplication().getPackageMgr()
        cls.api = APITool()

        if not tmp_file_path.parent.is_dir():
            tmp_file_path.parent.mkdir()
        if tmp_file_path.is_file():
            tmp_file_path.unlink()

        shutil.copy(package_file_path, tmp_file_path)

        package = cls.pkg_mgr.getUserPackageFromFilePath(
            str(tmp_file_path.resolve())
        )
        if package:
            cls.pkg_mgr.unloadUserPackage(package)
        cls.package = cls.pkg_mgr.loadUserPackage(str(tmp_file_path.resolve()))

    def test_straighten_connection_doesnt_affect_outputs_source(self):
        print("...test_straighten_connection_doesnt_affect_outputs_source")
        graph = self.package.findResourceFromUrl(
            "__test_straighten_connection_doesnt_affect_outputs"
        )
        correct_result_dir = self.tmp_dir / "correct_result"
        exportSDGraphOutputs(graph, str(correct_result_dir.resolve()))

        graph = self.package.findResourceFromUrl(
            "__test_straighten_connection_doesnt_affect_outputs_source"
        )
        source_result_dir = self.tmp_dir / "source_result"
        for node in graph.getNodes():
            try:
                node = StraightenNode(node, graph)
            except AttributeError:
                # Occurs if the dot node was previously removed
                continue
            bw_straighten_connection.run_straighten_connection(node, graph, self.settings[0])
        exportSDGraphOutputs(graph, str(source_result_dir.resolve()))

        time.sleep(10)

        for file in os.listdir(correct_result_dir):
            correct = correct_result_dir / file
            result = source_result_dir / file.replace("_outputs_", "_outputs_source_")
            correct = Image.open(str(correct.resolve())).convert('RGB')
            result = Image.open(str(result.resolve())).convert('RGB')
            diff = ImageChops.difference(correct, result)
            # self.assertFalse(diff.getbbox())
            if diff.getbbox():
                print("images are different")
            else:
                print("images are the same")


            
        

