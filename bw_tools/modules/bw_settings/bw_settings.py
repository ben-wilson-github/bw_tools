import importlib
import json
import operator
import os
from dataclasses import dataclass
from functools import reduce
from pathlib import Path
from typing import Any, Dict, List
import unittest

from bw_tools.modules.bw_settings import bw_settings_dialog
from tests import run_unit_tests, reload_modules
from PySide2 import QtGui

importlib.reload(bw_settings_dialog)


@dataclass
class ModuleSettings:
    file_path: Path

    @staticmethod
    def _get_from_dict(data: Dict, keys: List[str]):
        return reduce(operator.getitem, keys, data)

    def get(self, setting: str) -> Any:
        try:
            with open(self.file_path) as settings_file:
                data = json.load(settings_file)
        except FileNotFoundError:
            raise FileNotFoundError(
                f"Unable to open {self.file_path}. The file was not found"
            )

        keys = setting.split(";")

        try:
            ret = self._get_from_dict(data, keys)
        except KeyError:
            raise KeyError(
                f"Unable to get {setting} from settings file. "
                "It was not found inside the file."
            )

        except FileNotFoundError:
            raise FileNotFoundError(
                f"Unable to open {self.file_path}. The file was not found"
            )
        else:
            return ret


class Settings(ModuleSettings):
    def __init__(self, file_path: Path):
        super().__init__(file_path)
        self.dev_mode: bool = self.get("Dev Mode;value")


def on_initialize(api):
    settings_action = api.menu.addAction("Settings...")
    settings_action.setToolTip("BW Tools Settings")
    settings_action.triggered.connect(lambda: on_clicked_settings(api))

    settings = Settings(Path(__file__).parent / "bw_settings_settings.json")
    if settings.dev_mode:
        api.menu.addSeparator()
        unit_test_action = api.menu.addAction("Run unit tests...")
        unit_test_action.triggered.connect(lambda: run_unit_tests.run())

        reload_modules_action = api.menu.addAction("Reload modules...")
        reload_modules_action.triggered.connect(
            lambda: reload_modules.reload_modules()
        )


def on_clicked_settings(api):
    dialog = bw_settings_dialog.SettingsDialog(api)
    dialog.show()
