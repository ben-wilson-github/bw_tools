from bw_tools.modules.bw_settings.bw_settings import ModuleSettings
from pathlib import Path


def init():
    global settings_file
    settings_file = ModuleSettings(
        Path(__file__).parent / "bw_layout_graph_settings.json"
    )
