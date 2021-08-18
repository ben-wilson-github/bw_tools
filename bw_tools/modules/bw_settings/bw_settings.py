import importlib
import json
import operator
import os
from dataclasses import dataclass
from functools import reduce
from pathlib import Path
from typing import Any, Dict, List

from bw_tools.modules.bw_settings import bw_settings_dialog
from PySide2 import QtGui

importlib.reload(bw_settings_dialog)


@dataclass
class ModuleSettings:
    file_path: Path

    @staticmethod
    def _get_from_dict(data: Dict, keys: List[str]):
        return reduce(operator.getitem, keys, data)

    def get(self, setting: str) -> Any:
        NEED TO UPDATE THIS WITH CHANGES FROM SETTINGS FILE FORMAT
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


def on_initialize(api):
    resource_dir = os.path.normpath(
        f"{os.path.dirname(__file__)}\\.\\resources"
    )
    icon_path = os.path.join(resource_dir, "settings_icon.png")

    if api.debug:
        api.logger.debug("Adding settings action to toolbar.")
    settings_action = api.toolbar.addAction(QtGui.QIcon(icon_path), "")
    settings_action.setToolTip("BW Tools Settings")
    settings_action.triggered.connect(lambda: on_clicked_settings(api))


def on_clicked_settings(api):
    if api.debug:
        api.logger.debug("Opened settings dialog window.")

    dialog = bw_settings_dialog.SettingsDialog(api)
    dialog.show()
