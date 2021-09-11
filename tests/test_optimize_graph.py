from bw_tools.common.bw_api_tool import APITool
from bw_tools.common.bw_node_selection import NodeSelection
import unittest
from unittest.mock import Mock
from pathlib import Path
import shutil

import sd

from bw_tools.modules.bw_optimize_graph import bw_optimize_graph


class TestOptimizeGraph(unittest.TestCase):
    pkg_mgr = None
    package = None
    package_file_path = None
    tmp_package_file_path = None

    @classmethod
    def setUpClass(cls) -> None:
        cls.package_file_path = (
            Path(__file__).parent / "resources" / "test_optimize_graph.sbs"
        )
        cls.tmp_package_file_path = (
            Path(__file__).parent
            / "resources"
            / "tmp"
            / "__test_optimize_graph.sbs"
        )
        cls.pkg_mgr = sd.getContext().getSDApplication().getPackageMgr()

        if not cls.tmp_package_file_path.parent.is_dir():
            cls.tmp_package_file_path.parent.mkdir()
        if cls.tmp_package_file_path.is_file():
            cls.tmp_package_file_path.unlink()

        shutil.copy(cls.package_file_path, cls.tmp_package_file_path)

        cls.package = cls.pkg_mgr.getUserPackageFromFilePath(
            str(cls.tmp_package_file_path.resolve())
        )
        if cls.package:
            cls.pkg_mgr.unloadUserPackage(cls.package)
        cls.package = cls.pkg_mgr.loadUserPackage(
            str(cls.tmp_package_file_path.resolve())
        )
        cls.api = APITool()

    def test_deletes_uniform_color_node(self):
        graph_name = "test_deletes_uniform_color_node"
        print(f"...{graph_name}")

        settings = Mock()
        settings.uniform_force_output_size = False
        settings.recursive = True
        settings.popup_on_complete = False

        graph = self.package.findResourceFromUrl(graph_name)
        node_selection = NodeSelection(graph.getNodes(), graph)
        bw_optimize_graph.run(node_selection, self.api, settings)

        self.assertEqual(len(graph.getNodes()), 4)

    def test_does_not_delete_uniform_color_node_1(self):
        graph_name = "test_does_not_delete_uniform_color_node_1"
        print(f"...{graph_name}")

        settings = Mock()
        settings.uniform_force_output_size = False
        settings.recursive = True
        settings.popup_on_complete = False

        graph = self.package.findResourceFromUrl(graph_name)
        node_selection = NodeSelection(graph.getNodes(), graph)
        bw_optimize_graph.run(node_selection, self.api, settings)

        self.assertEqual(len(graph.getNodes()), 5)

    def test_does_not_delete_uniform_color_node_2(self):
        graph_name = "test_does_not_delete_uniform_color_node_2"
        print(f"...{graph_name}")

        settings = Mock()
        settings.uniform_force_output_size = False
        settings.recursive = True
        settings.popup_on_complete = False

        graph = self.package.findResourceFromUrl(graph_name)
        node_selection = NodeSelection(graph.getNodes(), graph)
        bw_optimize_graph.run(node_selection, self.api, settings)

        self.assertEqual(len(graph.getNodes()), 5)

    def test_uniform_color_node_output_size_and_sets_outputs_to_parent(
        self,
    ):
        graph_name = (
            "test_uniform_color_node_output_size_and_sets_outputs_to_parent"
        )
        print(f"...{graph_name}")

        settings = Mock()
        settings.uniform_force_output_size = True
        settings.recursive = True
        settings.popup_on_complete = False

        graph = self.package.findResourceFromUrl(graph_name)
        uniform_node = graph.getNodeFromId("1422819514")
        out1 = graph.getNodeFromId("1423425425")
        out2 = graph.getNodeFromId("1423425481")

        node_selection = NodeSelection(graph.getNodes(), graph)
        bw_optimize_graph.run(node_selection, self.api, settings)

        inheritance = uniform_node.getInputPropertyInheritanceMethodFromId(
            "$outputsize"
        )
        value = uniform_node.getInputPropertyValueFromId("$outputsize")
        self.assertEqual(
            inheritance, sd.api.sdproperty.SDPropertyInheritanceMethod.Absolute
        )
        self.assertEqual(value.get().x, 4)
        self.assertEqual(value.get().y, 4)

        inheritance = out1.getInputPropertyInheritanceMethodFromId(
            "$outputsize"
        )
        value = out1.getInputPropertyValueFromId("$outputsize")
        self.assertEqual(
            inheritance,
            sd.api.sdproperty.SDPropertyInheritanceMethod.RelativeToParent,
        )
        self.assertEqual(value.get().x, 0)
        self.assertEqual(value.get().y, 0)

        inheritance = out2.getInputPropertyInheritanceMethodFromId(
            "$outputsize"
        )
        value = out2.getInputPropertyValueFromId("$outputsize")
        self.assertEqual(
            inheritance,
            sd.api.sdproperty.SDPropertyInheritanceMethod.RelativeToParent,
        )
        self.assertEqual(value.get().x, 0)
        self.assertEqual(value.get().y, 0)

    def test_uniform_color_node_output_size_and_does_not_set_outputs(
        self,
    ):
        graph_name = (
            "test_uniform_color_node_output_size_and_does_not_set_outputs"
        )
        print(f"...{graph_name}")

        settings = Mock()
        settings.uniform_force_output_size = True
        settings.recursive = True
        settings.popup_on_complete = False

        graph = self.package.findResourceFromUrl(graph_name)
        uniform_node = graph.getNodeFromId("1422819514")
        out1 = graph.getNodeFromId("1423425425")
        out2 = graph.getNodeFromId("1423426484")

        node_selection = NodeSelection(graph.getNodes(), graph)
        bw_optimize_graph.run(node_selection, self.api, settings)

        inheritance = uniform_node.getInputPropertyInheritanceMethodFromId(
            "$outputsize"
        )
        value = uniform_node.getInputPropertyValueFromId("$outputsize")
        self.assertEqual(
            inheritance, sd.api.sdproperty.SDPropertyInheritanceMethod.Absolute
        )
        self.assertEqual(value.get().x, 4)
        self.assertEqual(value.get().y, 4)

        inheritance = out1.getInputPropertyInheritanceMethodFromId(
            "$outputsize"
        )
        value = out1.getInputPropertyValueFromId("$outputsize")
        self.assertEqual(
            inheritance,
            sd.api.sdproperty.SDPropertyInheritanceMethod.Absolute,
        )
        self.assertEqual(value.get().x, 7)
        self.assertEqual(value.get().y, 7)

        inheritance = out2.getInputPropertyInheritanceMethodFromId(
            "$outputsize"
        )
        value = out2.getInputPropertyValueFromId("$outputsize")
        self.assertTrue(
            inheritance,
            sd.api.sdproperty.SDPropertyInheritanceMethod.RelativeToParent,
        )
        self.assertEqual(value.get().x, 0)
        self.assertEqual(value.get().y, 0)

    def test_deletes_comp_graph_node(self):
        graph_name = "test_deletes_comp_graph_node"
        print(f"...{graph_name}")

        settings = Mock()
        settings.uniform_force_output_size = False
        settings.recursive = True
        settings.popup_on_complete = False

        graph = self.package.findResourceFromUrl(graph_name)
        node_selection = NodeSelection(graph.getNodes(), graph)
        bw_optimize_graph.run(node_selection, self.api, settings)

        self.assertEqual(len(graph.getNodes()), 2)

    def test_deletes_chain(self):
        graph_name = "test_deletes_chain"
        print(f"...{graph_name}")

        settings = Mock()
        settings.uniform_force_output_size = False
        settings.recursive = True
        settings.popup_on_complete = False

        graph = self.package.findResourceFromUrl(graph_name)
        node_selection = NodeSelection(graph.getNodes(), graph)
        bw_optimize_graph.run(node_selection, self.api, settings)

        self.assertEqual(len(graph.getNodes()), 5)

    def test_deletes_chain_no_recursion(self):
        graph_name = "test_deletes_chain_no_recursion"
        print(f"...{graph_name}")

        settings = Mock()
        settings.uniform_force_output_size = False
        settings.recursive = False
        settings.popup_on_complete = False

        graph = self.package.findResourceFromUrl(graph_name)
        node_selection = NodeSelection(graph.getNodes(), graph)
        bw_optimize_graph.run(node_selection, self.api, settings)

        self.assertEqual(len(graph.getNodes()), 7)

    def test_does_not_delete_chain(self):
        graph_name = "test_does_not_delete_chain"
        print(f"...{graph_name}")

        settings = Mock()
        settings.uniform_force_output_size = False
        settings.recursive = False
        settings.popup_on_complete = False

        graph = self.package.findResourceFromUrl(graph_name)
        node_selection = NodeSelection(graph.getNodes(), graph)
        bw_optimize_graph.run(node_selection, self.api, settings)

        self.assertEqual(len(graph.getNodes()), 7)


if __name__ == "__main__":
    unittest.main()
