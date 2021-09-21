import functools
import logging
import math
import operator
import os
import shutil
import time
import unittest
from pathlib import Path
from unittest.mock import Mock

import sd
from bw_tools.common.bw_api_tool import BWAPITool, FunctionNodeId
from bw_tools.modules.bw_straighten_connection import bw_straighten_connection
from bw_tools.modules.bw_straighten_connection.straighten_behavior import (
    BWBreakAtSource,
    BWBreakAtTarget,
)
from bw_tools.modules.bw_straighten_connection.straighten_node import (
    StraightenNode,
)
from PIL import Image, ImageChops
from sd.tools.export import exportSDGraphOutputs


class TestStraightenConnection(unittest.TestCase):
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

        cls.settings = Mock()
        cls.settings.dot_node_distance = 128

        cls.pkg_mgr = sd.getContext().getSDApplication().getPackageMgr()
        cls.api = BWAPITool()

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

        cls.correct_result_dir = cls.tmp_dir / "correct_result"
        cls.source_result_dir = cls.tmp_dir / "source_result"
        cls.target_result_dir = cls.tmp_dir / "target_result"
        for folder in [
            cls.correct_result_dir,
            cls.source_result_dir,
            cls.target_result_dir,
        ]:
            for f in os.listdir(folder):
                path = folder / f
                path.unlink()

        _run_render_textures(
            cls.package,
            cls.correct_result_dir,
            cls.source_result_dir,
            cls.target_result_dir,
            cls.settings,
        )
        _wait_for_files_to_render(
            cls.correct_result_dir,
            cls.source_result_dir,
            cls.target_result_dir,
        )
        logging.getLogger("PIL.PngImagePlugin").setLevel(logging.WARNING)

    def test_straighten_connection_doesnt_affect_outputs_source(self):
        print("...test_straighten_connection_doesnt_affect_outputs_source")
        self._run_test_outputs_are_the_same(
            self.source_result_dir, "_outputs_source_"
        )

    def test_straighten_connection_doesnt_affect_outputs_target(self):
        print("...test_straighten_connection_doesnt_affect_outputs_target")
        self._run_test_outputs_are_the_same(
            self.target_result_dir, "_outputs_target_"
        )

    def test_straighten_connection_1_source(self):
        print("...test_straighten_connection_1_source")
        result_graph = self.package.findResourceFromUrl(
            "test_straighten_connection_1_result_source"
        )
        correct_graph = self.package.findResourceFromUrl(
            "test_straighten_connection_1_correct_source"
        )
        self._run_test_graph(
            result_graph,
            correct_graph,
            BWBreakAtSource(result_graph),
            self.settings,
        )

    def test_straighten_connection_1_target(self):
        print("...test_straighten_connection_1_target")
        result_graph = self.package.findResourceFromUrl(
            "test_straighten_connection_1_result_target"
        )
        correct_graph = self.package.findResourceFromUrl(
            "test_straighten_connection_1_correct_target"
        )
        self._run_test_graph(
            result_graph,
            correct_graph,
            BWBreakAtTarget(result_graph),
            self.settings,
        )

    def test_straighten_connection_2_source(self):
        print("...test_straighten_connection_2_source")
        result_graph = self.package.findResourceFromUrl(
            "test_straighten_connection_2_result_source"
        )
        correct_graph = self.package.findResourceFromUrl(
            "test_straighten_connection_2_correct_source"
        )
        self._run_test_graph(
            result_graph,
            correct_graph,
            BWBreakAtSource(result_graph),
            self.settings,
        )

    def test_straighten_connection_2_target(self):
        print("...test_straighten_connection_2_target")
        result_graph = self.package.findResourceFromUrl(
            "test_straighten_connection_2_result_target"
        )
        correct_graph = self.package.findResourceFromUrl(
            "test_straighten_connection_2_correct_target"
        )
        self._run_test_graph(
            result_graph,
            correct_graph,
            BWBreakAtTarget(result_graph),
            self.settings,
        )

    def test_straighten_connection_3_source(self):
        print("...test_straighten_connection_3_source")
        result_graph = self.package.findResourceFromUrl(
            "test_straighten_connection_3_result_source"
        )
        correct_graph = self.package.findResourceFromUrl(
            "test_straighten_connection_3_correct_source"
        )
        self._run_test_graph(
            result_graph,
            correct_graph,
            BWBreakAtSource(result_graph),
            self.settings,
        )

    def test_straighten_connection_3_target(self):
        print("...test_straighten_connection_3_target")
        result_graph = self.package.findResourceFromUrl(
            "test_straighten_connection_3_result_target"
        )
        correct_graph = self.package.findResourceFromUrl(
            "test_straighten_connection_3_correct_target"
        )
        self._run_test_graph(
            result_graph,
            correct_graph,
            BWBreakAtTarget(result_graph),
            self.settings,
        )

    def test_straighten_connection_4_source(self):
        print("...test_straighten_connection_4_source")
        result_graph = self.package.findResourceFromUrl(
            "test_straighten_connection_4_result_source"
        )
        correct_graph = self.package.findResourceFromUrl(
            "test_straighten_connection_4_correct_source"
        )
        self._run_test_graph(
            result_graph,
            correct_graph,
            BWBreakAtSource(result_graph),
            self.settings,
        )

    def test_straighten_connection_4_target(self):
        print("...test_straighten_connection_4_target")
        result_graph = self.package.findResourceFromUrl(
            "test_straighten_connection_4_result_target"
        )
        correct_graph = self.package.findResourceFromUrl(
            "test_straighten_connection_4_correct_target"
        )
        self._run_test_graph(
            result_graph,
            correct_graph,
            BWBreakAtTarget(result_graph),
            self.settings,
        )

    def test_straighten_connection_5_source(self):
        print("...test_straighten_connection_5_source")
        result_graph = self.package.findResourceFromUrl(
            "test_straighten_connection_5_result_source"
        )
        correct_graph = self.package.findResourceFromUrl(
            "test_straighten_connection_5_correct_source"
        )
        self._run_test_graph(
            result_graph,
            correct_graph,
            BWBreakAtSource(result_graph),
            self.settings,
        )

    def test_straighten_connection_5_target(self):
        print("...test_straighten_connection_5_target")
        result_graph = self.package.findResourceFromUrl(
            "test_straighten_connection_5_result_target"
        )
        correct_graph = self.package.findResourceFromUrl(
            "test_straighten_connection_5_correct_target"
        )
        self._run_test_graph(
            result_graph,
            correct_graph,
            BWBreakAtTarget(result_graph),
            self.settings,
        )

    def test_straighten_connection_6_source(self):
        print("...test_straighten_connection_6_source")
        result_graph = self.package.findResourceFromUrl(
            "test_straighten_connection_6_result_source"
        )
        correct_graph = self.package.findResourceFromUrl(
            "test_straighten_connection_6_correct_source"
        )
        self._run_test_graph(
            result_graph,
            correct_graph,
            BWBreakAtSource(result_graph),
            self.settings,
        )

    def test_straighten_connection_6_target(self):
        print("...test_straighten_connection_6_target")
        result_graph = self.package.findResourceFromUrl(
            "test_straighten_connection_6_result_target"
        )
        correct_graph = self.package.findResourceFromUrl(
            "test_straighten_connection_6_correct_target"
        )
        self._run_test_graph(
            result_graph,
            correct_graph,
            BWBreakAtTarget(result_graph),
            self.settings,
        )

    def test_can_run_on_function_graph(self):
        print("...test_can_run_on_function_graph")
        # Expected graph
        expected_graph = self.package.findResourceFromUrl(
            "test_can_run_on_function_graph_expected"
        )
        node = expected_graph.getNodes()[0]
        property = node.getPropertyFromId(
            "perpixel", sd.api.sdproperty.SDPropertyCategory.Input
        )
        expected_px_graph = expected_graph.getNodes()[0].getPropertyGraph(
            property
        )

        # Test graph
        test_graph = self.package.findResourceFromUrl(
            "test_can_run_on_function_graph"
        )
        node = test_graph.getNodes()[0]
        property = node.getPropertyFromId(
            "perpixel", sd.api.sdproperty.SDPropertyCategory.Input
        )
        test_px_graph = test_graph.getNodes()[0].getPropertyGraph(property)

        _run_straighten(
            test_px_graph, BWBreakAtTarget(test_px_graph), self.settings
        )

        test_dot_node = [
            n
            for n in test_px_graph.getNodes()
            if n.getDefinition().getId() == FunctionNodeId.DOT.value
        ]
        expected_dot_node = [
            n
            for n in expected_px_graph.getNodes()
            if n.getDefinition().getId() == FunctionNodeId.DOT.value
        ]
        self.assertTrue(
            math.isclose(
                test_dot_node[0].getPosition().x,
                expected_dot_node[0].getPosition().x,
            )
        )
        self.assertTrue(
            math.isclose(
                test_dot_node[0].getPosition().y,
                expected_dot_node[0].getPosition().y,
            )
        )

    def _run_test_outputs_are_the_same(self, output_dir, str_replace):
        """
        The graphs are precalulated and exported in the setupClass function
        """
        for file in os.listdir(self.correct_result_dir):
            correct = self.correct_result_dir / file
            result = output_dir / file.replace("_outputs_", str_replace)
            correct = Image.open(str(correct.resolve())).convert("RGB")
            result = Image.open(str(result.resolve())).convert("RGB")
            rms = _calculate_rms(correct, result)
            # Designer doesnt render the same each time, so difference might
            # be slightly off
            self.assertAlmostEqual(rms, 0, places=1)

    def _run_test_graph(self, result_graph, correct_graph, behavior, settings):
        _run_straighten(result_graph, behavior, settings)

        results_nodes = [
            StraightenNode(n, result_graph) for n in result_graph.getNodes()
        ]
        for result_node in results_nodes:
            self.assertTrue(
                any(
                    math.isclose(
                        result_node.pos.x, node.getPosition().x, abs_tol=0.1
                    )
                    for node in correct_graph.getNodes()
                )
            )
            self.assertTrue(
                any(
                    math.isclose(
                        result_node.pos.y, node.getPosition().y, abs_tol=0.1
                    )
                    for node in correct_graph.getNodes()
                )
            )


def _wait_for_files_to_render(
    correct_result_dir, source_result_dir, target_result_dir
):
    ready = False
    for _ in range(10):
        ready = True
        for folder in [
            correct_result_dir,
            source_result_dir,
            target_result_dir,
        ]:
            for f in os.listdir(folder):
                file = folder / f
                if not _check_file(file):
                    ready = False
                    break

            if not ready:
                break

        if ready:
            print("textures rendered")
            return True
        print("waiting for renders to finish")
        time.sleep(1)
    return False


def _run_render_textures(
    package, correct_result_dir, source_result_dir, target_result_dir, settings
):
    graph = package.findResourceFromUrl(
        "__test_straighten_connection_doesnt_affect_outputs"
    )
    exportSDGraphOutputs(graph, str(correct_result_dir.resolve()))

    graph = package.findResourceFromUrl(
        "__test_straighten_connection_doesnt_affect_outputs_source"
    )
    _run_straighten(graph, BWBreakAtSource(graph), settings)
    exportSDGraphOutputs(graph, str(source_result_dir.resolve()))

    graph = package.findResourceFromUrl(
        "__test_straighten_connection_doesnt_affect_outputs_target"
    )
    _run_straighten(graph, BWBreakAtTarget(graph), settings)
    exportSDGraphOutputs(graph, str(target_result_dir.resolve()))


def _run_straighten(graph, behavior, settings):
    for node in graph.getNodes():
        try:
            node = StraightenNode(node, graph)
        except AttributeError:
            # Occurs if the dot node was previously removed
            continue
        bw_straighten_connection.run_straighten_connection(
            node, behavior, settings
        )


def _calculate_rms(im1: Image, im2: Image) -> float:
    h = ImageChops.difference(im1, im2).histogram()
    return math.sqrt(
        functools.reduce(
            operator.add,
            map(lambda h, i: i % 256 * (h ** 2), h, range(len(h))),
        )
        / (float(im1.size[0]) * im1.size[1])
    )


def _check_file(f: Path):
    return f.exists() and f.stat().st_size >= 75
