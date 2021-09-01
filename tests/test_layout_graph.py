import copy
import random
import shutil
import unittest
from pathlib import Path
from typing import Dict
from unittest.mock import Mock

import sd
from bw_tools.common import bw_node_selection
from bw_tools.common.bw_api_tool import APITool
from bw_tools.modules.bw_layout_graph import bw_layout_graph
from bw_tools.modules.bw_layout_graph.layout_node import (
    LayoutNode,
    LayoutNodeSelection,
)


class TestLayoutGraphMainlineEnabledMainlineAlign(unittest.TestCase):
    packages = None
    settings = None
    pkg_mgr = None

    @classmethod
    def setUpClass(cls) -> None:
        print("...Setting up class")
        cls.packages = []

        current_dir = Path(__file__).parent
        package_file_paths = [
            current_dir
            / "resources"
            / "test_layout_graph_mainline_enabled_mainline_align.sbs",
            current_dir
            / "resources"
            / "test_layout_graph_mainline_enabled_center_align.sbs",
            current_dir
            / "resources"
            / "test_layout_graph_mainline_enabled_top_align.sbs",
            current_dir
            / "resources"
            / "test_layout_graph_mainline_disabled_mainline_align.sbs",
            current_dir
            / "resources"
            / "test_layout_graph_mainline_disabled_center_align.sbs",
            current_dir
            / "resources"
            / "test_layout_graph_mainline_disabled_top_align.sbs",
            current_dir
            / "resources"
            / "test_layout_graph_mainline_enabled_no_additional_offset.sbs",
            current_dir
            / "resources"
            / "test_layout_graph_mainline_enabled_node_spacing_128.sbs",
            current_dir
            / "resources"
            / "test_layout_graph_mainline_enabled_min_ml_threshold_0.sbs",
        ]
        tmp_file_paths = [
            current_dir
            / "resources"
            / "tmp"
            / "__test_layout_graph_mainline_enabled_mainline_align.sbs",
            current_dir
            / "resources"
            / "tmp"
            / "__test_layout_graph_mainline_enabled_center_align.sbs",
            current_dir
            / "resources"
            / "tmp"
            / "__test_layout_graph_mainline_enabled_top_align.sbs",
            current_dir
            / "resources"
            / "tmp"
            / "__test_layout_graph_mainline_disabled_mainline_align.sbs",
            current_dir
            / "resources"
            / "tmp"
            / "__test_layout_graph_mainline_disabled_center_align.sbs",
            current_dir
            / "resources"
            / "tmp"
            / "__test_layout_graph_mainline_disabled_top_align.sbs",
            current_dir
            / "resources"
            / "tmp"
            / "__test_layout_graph_mainline_enabled_no_additional_offset.sbs",
            current_dir
            / "resources"
            / "tmp"
            / "__test_layout_graph_mainline_enabled_node_spacing_128.sbs",
            current_dir
            / "resources"
            / "tmp"
            / "__test_layout_graph_mainline_enabled_min_ml_threshold_0.sbs",
        ]

        s1 = Mock()
        s1.mainline_enabled = True
        s1.hotkey = "C"
        s1.node_spacing = 32.0
        s1.mainline_additional_offset = 96.0
        s1.mainline_min_threshold = 96
        s1.alignment_behavior = 0
        s1.run_straighten_connection = False
        s1.snap_to_grid = False

        s2 = Mock()
        s2.mainline_enabled = True
        s2.hotkey = "C"
        s2.node_spacing = 32.0
        s2.mainline_additional_offset = 96.0
        s2.mainline_min_threshold = 96
        s2.alignment_behavior = 1
        s2.run_straighten_connection = False
        s2.snap_to_grid = False

        s3 = Mock()
        s3.mainline_enabled = True
        s3.hotkey = "C"
        s3.node_spacing = 32.0
        s3.mainline_additional_offset = 96.0
        s3.mainline_min_threshold = 96
        s3.alignment_behavior = 2
        s3.run_straighten_connection = False
        s3.snap_to_grid = False

        s4 = Mock()
        s4.mainline_enabled = False
        s4.hotkey = "C"
        s4.node_spacing = 32.0
        s4.mainline_additional_offset = 96.0
        s4.mainline_min_threshold = 96
        s4.alignment_behavior = 0
        s4.run_straighten_connection = False
        s4.snap_to_grid = False

        s5 = Mock()
        s5.mainline_enabled = False
        s5.hotkey = "C"
        s5.node_spacing = 32.0
        s5.mainline_additional_offset = 96.0
        s5.mainline_min_threshold = 96
        s5.alignment_behavior = 1
        s5.run_straighten_connection = False
        s5.snap_to_grid = False

        s6 = Mock()
        s6.mainline_enabled = False
        s6.hotkey = "C"
        s6.node_spacing = 32.0
        s6.mainline_additional_offset = 96.0
        s6.mainline_min_threshold = 96
        s6.alignment_behavior = 2
        s6.run_straighten_connection = False
        s6.snap_to_grid = False

        s7 = Mock()
        s7.mainline_enabled = True
        s7.hotkey = "C"
        s7.node_spacing = 32.0
        s7.mainline_additional_offset = 0.0
        s7.mainline_min_threshold = 96
        s7.alignment_behavior = 0
        s7.run_straighten_connection = False
        s7.snap_to_grid = False

        s8 = Mock()
        s8.mainline_enabled = True
        s8.hotkey = "C"
        s8.node_spacing = 128.0
        s8.mainline_additional_offset = 96.0
        s8.mainline_min_threshold = 96
        s8.alignment_behavior = 0
        s8.run_straighten_connection = False
        s8.snap_to_grid = False

        s9 = Mock()
        s9.mainline_enabled = True
        s9.hotkey = "C"
        s9.node_spacing = 128.0
        s9.mainline_additional_offset = 96.0
        s9.mainline_min_threshold = 0
        s9.alignment_behavior = 0
        s9.run_straighten_connection = False
        s9.snap_to_grid = False

        cls.settings = [s1, s2, s3, s4, s5, s6, s7, s8, s9]

        cls.pkg_mgr = sd.getContext().getSDApplication().getPackageMgr()
        cls.api = APITool()

        for i, tmp_file in enumerate(tmp_file_paths):
            if not tmp_file.parent.is_dir():
                tmp_file.parent.mkdir()
            if tmp_file.is_file():
                tmp_file.unlink()

            shutil.copy(package_file_paths[i], tmp_file)

            package = cls.pkg_mgr.getUserPackageFromFilePath(
                str(tmp_file.resolve())
            )
            if package:
                cls.pkg_mgr.unloadUserPackage(package)
            package = cls.pkg_mgr.loadUserPackage(str(tmp_file.resolve()))
            cls.packages.append(package)
    
    def test_no_nodes_does_not_throw_error_mainline_enabled_mainline_align(
        self,
    ):
        print(
            "...test_no_nodes_does_not_throw_error_mainline_enabled_mainline_align"
        )
        package = self.packages[0]
        settings = self.settings[0]
        self.run_no_nodes_does_not_throw_error(package, settings)

    def test_no_nodes_does_not_throw_error_mainline_enabled_center_align(
        self,
    ):
        print(
            "...test_no_nodes_does_not_throw_error_mainline_enabled_center_align"
        )
        package = self.packages[0]
        settings = self.settings[1]
        self.run_no_nodes_does_not_throw_error(package, settings)

    def test_no_nodes_does_not_throw_error_mainline_enabled_top_align(
        self,
    ):
        print(
            "...test_no_nodes_does_not_throw_error_mainline_enabled_top_align"
        )
        package = self.packages[0]
        settings = self.settings[2]
        self.run_no_nodes_does_not_throw_error(package, settings)

    def test_removes_dot_nodes(self):
        print("...test_removes_dot_nodes")
        graph_name = "test_removes_dot_nodes"
        graph = self.packages[0].findResourceFromUrl(graph_name)
        bw_node_selection.remove_dot_nodes(graph.getNodes(), graph)
        self.run_layout_test_on_graph(graph, self.settings[0])

    def test_single_node(self):
        print("...test_single_node")
        graph = self.packages[0].findResourceFromUrl("test_single_node")
        node_selection = LayoutNodeSelection(graph.getNodes(), graph)
        bw_layout_graph.run_layout(node_selection, self.api, self.settings[0])
        self.assertTrue(True)

    def test_node_chain_1(self):
        graph_name = "test_node_chain_1"
        print(f"...{graph_name}")
        self.run_layout_test_on_graph(
            self.packages[0].findResourceFromUrl(graph_name), self.settings[0]
        )

    def test_node_chain_2(self):
        graph_name = "test_node_chain_2"
        print(f"...{graph_name}")
        self.run_layout_test_on_graph(
            self.packages[0].findResourceFromUrl(graph_name), self.settings[0]
        )

    def test_node_chain_3(self):
        graph_name = "test_node_chain_3"
        print(f"...{graph_name}")
        self.run_layout_test_on_graph(
            self.packages[0].findResourceFromUrl(graph_name), self.settings[0]
        )

    def test_node_chain_4(self):
        graph_name = "test_node_chain_4"
        print(f"...{graph_name}")
        self.run_layout_test_on_graph(
            self.packages[0].findResourceFromUrl(graph_name), self.settings[0]
        )

    def test_node_chain_5(self):
        graph_name = "test_node_chain_5"
        print(f"...{graph_name}")
        self.run_layout_test_on_graph(
            self.packages[0].findResourceFromUrl(graph_name), self.settings[0]
        )

    def test_node_chain_6(self):
        graph_name = "test_node_chain_6"
        print(f"...{graph_name}")
        self.run_layout_test_on_graph(
            self.packages[0].findResourceFromUrl(graph_name), self.settings[0]
        )

    def test_node_chain_7(self):
        graph_name = "test_node_chain_7"
        print(f"...{graph_name}")
        self.run_layout_test_on_graph(
            self.packages[0].findResourceFromUrl(graph_name), self.settings[0]
        )

    def test_node_chain_8(self):
        graph_name = "test_node_chain_8"
        print(f"...{graph_name}")
        self.run_layout_test_on_graph(
            self.packages[0].findResourceFromUrl(graph_name), self.settings[0]
        )

    def test_node_chain_9(self):
        graph_name = "test_node_chain_9"
        print(f"...{graph_name}")
        self.run_layout_test_on_graph(
            self.packages[0].findResourceFromUrl(graph_name), self.settings[0]
        )

    def test_node_chain_10(self):
        graph_name = "test_node_chain_10"
        print(f"...{graph_name}")
        self.run_layout_test_on_graph(
            self.packages[0].findResourceFromUrl(graph_name), self.settings[0]
        )

    def test_node_chain_11(self):
        graph_name = "test_node_chain_11"
        print(f"...{graph_name}")
        self.run_layout_test_on_graph(
            self.packages[0].findResourceFromUrl(graph_name), self.settings[0]
        )

    def test_node_chain_12(self):
        graph_name = "test_node_chain_12"
        print(f"...{graph_name}")
        self.run_layout_test_on_graph(
            self.packages[0].findResourceFromUrl(graph_name), self.settings[0]
        )

    def test_node_chain_13(self):
        graph_name = "test_node_chain_13"
        print(f"...{graph_name}")
        self.run_layout_test_on_graph(
            self.packages[0].findResourceFromUrl(graph_name), self.settings[0]
        )

    def test_node_chain_14(self):
        graph_name = "test_node_chain_14"
        print(f"...{graph_name}")
        self.run_layout_test_on_graph(
            self.packages[0].findResourceFromUrl(graph_name), self.settings[0]
        )

    def test_node_chain_15(self):
        graph_name = "test_node_chain_15"
        print(f"...{graph_name}")
        self.run_layout_test_on_graph(
            self.packages[0].findResourceFromUrl(graph_name), self.settings[0]
        )

    def test_node_chain_16(self):
        graph_name = "test_node_chain_16"
        print(f"...{graph_name}")
        self.run_layout_test_on_graph(
            self.packages[0].findResourceFromUrl(graph_name), self.settings[0]
        )

    def test_node_chain_17(self):
        graph_name = "test_node_chain_17"
        print(f"...{graph_name}")
        self.run_layout_test_on_graph(
            self.packages[0].findResourceFromUrl(graph_name), self.settings[0]
        )

    def test_node_chain_18(self):
        graph_name = "test_node_chain_18"
        print(f"...{graph_name}")
        self.run_layout_test_on_graph(
            self.packages[0].findResourceFromUrl(graph_name), self.settings[0]
        )

    def test_node_chain_19(self):
        graph_name = "test_node_chain_19"
        print(f"...{graph_name}")
        self.run_layout_test_on_graph(
            self.packages[0].findResourceFromUrl(graph_name), self.settings[0]
        )

    def test_node_chain_20(self):
        graph_name = "test_node_chain_20"
        print(f"...{graph_name}")
        self.run_layout_test_on_graph(
            self.packages[0].findResourceFromUrl(graph_name), self.settings[0]
        )

    def test_node_chain_21(self):
        graph_name = "test_node_chain_21"
        print(f"...{graph_name}")
        self.run_layout_test_on_graph(
            self.packages[0].findResourceFromUrl(graph_name), self.settings[0]
        )

    def test_node_chain_22(self):
        graph_name = "test_node_chain_22"
        print(f"...{graph_name}")
        self.run_layout_test_on_graph(
            self.packages[0].findResourceFromUrl(graph_name), self.settings[0]
        )

    def test_node_chain_23(self):
        graph_name = "test_node_chain_23"
        print(f"...{graph_name}")
        self.run_layout_test_on_graph(
            self.packages[0].findResourceFromUrl(graph_name), self.settings[0]
        )

    def test_node_chain_24(self):
        graph_name = "test_node_chain_24"
        print(f"...{graph_name}")
        self.run_layout_test_on_graph(
            self.packages[0].findResourceFromUrl(graph_name), self.settings[0]
        )

    def test_node_chain_25_ml_on_align_ml(self):
        print("...test_node_chain_25_ml_on_align_ml")
        graph_name = "test_node_chain_25"
        self.run_layout_test_on_graph(
            self.packages[0].findResourceFromUrl(graph_name), self.settings[0]
        )

    def test_node_chain_25_ml_on_align_c(self):
        print("...test_node_chain_25_ml_on_align_c")
        graph_name = "test_node_chain_25"
        self.run_layout_test_on_graph(
            self.packages[1].findResourceFromUrl(graph_name), self.settings[1]
        )

    def test_node_chain_25_ml_on_align_t(self):
        print("...test_node_chain_25_ml_on_align_t")
        graph_name = "test_node_chain_25"
        self.run_layout_test_on_graph(
            self.packages[2].findResourceFromUrl(graph_name), self.settings[2]
        )

    def test_node_chain_25_ml_off_align_ml(self):
        print("...test_node_chain_25_ml_off_align_ml")
        graph_name = "test_node_chain_25"
        self.run_layout_test_on_graph(
            self.packages[3].findResourceFromUrl(graph_name), self.settings[3]
        )

    def test_node_chain_25_ml_off_align_c(self):
        print("...test_node_chain_25_ml_off_align_c")
        graph_name = "test_node_chain_25"
        self.run_layout_test_on_graph(
            self.packages[4].findResourceFromUrl(graph_name), self.settings[4]
        )

    def test_node_chain_25_ml_off_align_t(self):
        print("...test_node_chain_25_ml_off_align_t")
        graph_name = "test_node_chain_25"
        self.run_layout_test_on_graph(
            self.packages[5].findResourceFromUrl(graph_name), self.settings[5]
        )

    def test_node_chain_25_ml_on_align_ml_no_additional_offset(self):
        print("...test_node_chain_25_ml_on_align_ml_no_additional_offset")
        graph_name = "test_node_chain_25"
        self.run_layout_test_on_graph(
            self.packages[6].findResourceFromUrl(graph_name), self.settings[6]
        )

    def test_node_chain_25_ml_on_align_ml_node_spacing_128(self):
        print("...test_node_chain_25_ml_on_align_ml_node_spacing_128")
        graph_name = "test_node_chain_25"
        self.run_layout_test_on_graph(
            self.packages[7].findResourceFromUrl(graph_name), self.settings[7]
        )

    def test_layout_graph_mainline_enabled_min_ml_threshold_0(self):
        print("...test_layout_graph_mainline_enabled_min_ml_threshold_0")
        graph_name = "test_node_chain_20"
        self.run_layout_test_on_graph(
            self.packages[0].findResourceFromUrl(graph_name), self.settings[0]
        )

    def run_layout_test_on_graph(self, graph, settings):
        node_selection = LayoutNodeSelection(graph.getNodes(), graph)
        original_positions = self._get_node_positions(node_selection)

        self._randomise_node_positions(node_selection)
        bw_layout_graph.run_layout(node_selection, self.api, settings)

        new_positions = self._get_node_positions(node_selection)
        self.assertNodePositionsAreEqual(
            original_positions, new_positions, node_selection
        )

    def run_no_nodes_does_not_throw_error(self, package, settings):
        graph = package.findResourceFromUrl(
            "test_no_nodes_does_not_throw_error"
        )
        node_selection = LayoutNodeSelection([], graph)
        bw_layout_graph.run_layout(node_selection, self.api, settings)
        self.assertTrue(True)

    def assertNodePositionsAreEqual(
        self,
        original_positions,
        new_positions,
        node_selection: LayoutNodeSelection,
    ):
        for node in node_selection.nodes:
            self.assertAlmostEqual(
                original_positions[node.identifier].x,
                new_positions[node.identifier].x,
                places=2,
            )
            self.assertAlmostEqual(
                original_positions[node.identifier].y,
                new_positions[node.identifier].y,
                places=2,
            )

    def _get_node_positions(self, node_selection: LayoutNodeSelection) -> Dict:
        result = {}
        node: LayoutNode
        for node in node_selection.nodes:
            if node.is_dot:
                continue
            result[node.identifier] = copy.deepcopy(node.pos)
        return result

    def _randomise_node_positions(self, node_selection: LayoutNodeSelection):
        x = 300
        for node in node_selection.nodes:
            if node.is_root:
                continue
            node.set_position(
                node.pos.x + random.uniform(-x, x),
                node.pos.y + random.uniform(-x, x),
            )


if __name__ == "__main__":
    unittest.main()
