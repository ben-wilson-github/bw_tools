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
from bw_tools.common.bw_api_tool import APITool
from bw_tools.modules.bw_straighten_connection import bw_straighten_connection
from bw_tools.modules.bw_straighten_connection.straighten_node import (
    StraightenNode,
)
from PIL import Image, ImageChops
from sd.tools.export import exportSDGraphOutputs


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

        s2 = Mock()
        s2.dot_node_distance = 128
        s2.alignment_behavior = 1

        cls.settings = [s1, s2]

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

        cls.correct_result_dir = cls.tmp_dir / "correct_result"
        cls.source_result_dir = cls.tmp_dir / "source_result"
        cls.target_result_dir = cls.tmp_dir / "target_result"
        for folder in [
            cls.correct_result_dir,
            cls.source_result_dir,
            cls.target_result_dir,
        ]:
            shutil.rmtree(folder)

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
        _run_straighten(result_graph, self.settings[0])

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

    def test_straighten_connection_1_target(self):
        print("...test_straighten_connection_1_target")
        result_graph = self.package.findResourceFromUrl(
            "test_straighten_connection_1_result_target"
        )
        correct_graph = self.package.findResourceFromUrl(
            "test_straighten_connection_1_correct_target"
        )
        _run_straighten(result_graph, self.settings[1])

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

    def test_only_removes_nodes_in_node_selection(self):
        self.assertFalse(True)

    def _run_test_outputs_are_the_same(self, output_dir, str_replace):
        for file in os.listdir(self.correct_result_dir):
            correct = self.correct_result_dir / file
            result = output_dir / file.replace("_outputs_", str_replace)
            correct = Image.open(str(correct.resolve())).convert("RGB")
            result = Image.open(str(result.resolve())).convert("RGB")
            rms = _calculate_rms(correct, result)
            # Designer doesnt render the same each time, so difference might
            # be slightly off
            self.assertAlmostEqual(rms, 0, places=1)


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
    _run_straighten(graph, settings[0])
    exportSDGraphOutputs(graph, str(source_result_dir.resolve()))

    graph = package.findResourceFromUrl(
        "__test_straighten_connection_doesnt_affect_outputs_target"
    )
    _run_straighten(graph, settings[1])
    exportSDGraphOutputs(graph, str(target_result_dir.resolve()))


def _run_straighten(graph, settings):
    for node in graph.getNodes():
        try:
            node = StraightenNode(node, graph)
        except AttributeError:
            # Occurs if the dot node was previously removed
            continue
        bw_straighten_connection.run_straighten_connection(
            node, graph, settings
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
