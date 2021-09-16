import json
import operator
from dataclasses import dataclass
from functools import reduce
from pathlib import Path
from typing import Any, Dict, List

from bw_tools.modules.bw_settings import bw_settings_dialog


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

def on_clicked_settings(api):
    dialog = bw_settings_dialog.SettingsDialog(api)
    dialog.show()
