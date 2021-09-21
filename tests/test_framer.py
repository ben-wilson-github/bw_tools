import shutil
import unittest
from unittest.mock import Mock
from pathlib import Path

import sd
from bw_tools.common.bw_api_tool import BWAPITool
from bw_tools.modules.bw_framer import bw_framer


class TestFramer(unittest.TestCase):
    pkg_mgr = None
    package = None
    package_file_path = None

    @classmethod
    def setUpClass(cls) -> None:
        package_file_path = (
            Path(__file__).parent / "resources" / "test_framer.sbs"
        )
        tmp_package_file_path = (
            Path(__file__).parent / "resources" / "tmp" / "__test_framer.sbs"
        )

        if not tmp_package_file_path.parent.is_dir():
            tmp_package_file_path.parent.mkdir()
        if tmp_package_file_path.is_file():
            tmp_package_file_path.unlink()
        shutil.copy(package_file_path, tmp_package_file_path)

        pkg_mgr = sd.getContext().getSDApplication().getPackageMgr()

        cls.settings = Mock()
        cls.settings.margin = 32
        cls.settings.default_color = [0.0, 0.0, 0.0, 0.25]
        cls.settings.default_title = ""

        cls.package = pkg_mgr.getUserPackageFromFilePath(
            str(tmp_package_file_path.resolve())
        )
        if cls.package:
            pkg_mgr.unloadUserPackage(cls.package)
        cls.package = pkg_mgr.loadUserPackage(
            str(tmp_package_file_path.resolve())
        )
        cls.api = BWAPITool()

    def test_deletes_multiple_frames(self):
        print("...test_deletes_multiple_frames")
        graph = self.package.findResourceFromUrl(
            "test_deletes_multiple_frames"
        )
        nodes = graph.getNodes()
        graph_objects = graph.getGraphObjects()

        bw_framer.run_framer(nodes, graph_objects, graph, self.settings)

        graph_objects = graph.getGraphObjects()
        self.assertEqual(len(graph_objects), 1)

    def test_reuses_existing_frame(self):
        print("...test_reuses_existing_frame")
        graph = self.package.findResourceFromUrl("test_reuses_existing_frame")
        nodes = graph.getNodes()
        graph_objects = graph.getGraphObjects()

        bw_framer.run_framer(nodes, graph_objects, graph, self.settings)

        frame = graph.getGraphObjects()[0]
        self.assertEqual(frame.getDescription(), "with description")
        self.assertEqual(frame.getTitle(), "Frame1")
        self.assertEqual(frame.getSize().x, 345.0)
        self.assertEqual(frame.getSize().y, 256.0)

    def test_creates_new_frame(self):
        print("...test_creates_new_frame")
        graph = self.package.findResourceFromUrl("test_creates_new_frame")
        nodes = graph.getNodes()
        graph_objects = graph.getGraphObjects()

        bw_framer.run_framer(nodes, graph_objects, graph, self.settings)

        frame = graph.getGraphObjects()[0]
        self.assertEqual(frame.getTitle(), "")
        self.assertEqual(frame.getSize().x, 601.0)
        self.assertEqual(frame.getSize().y, 416.0)


if __name__ == "__main__":
    unittest.main()
