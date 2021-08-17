from pathlib import Path

from bw_tools.modules.bw_settings.bw_settings import ModuleSettings


def init():
    global LAYOUT_SETTINGS
    global HOTKEY
    global NODE_SPACING
    global MAINLINE_ADDITIONAL_OFFSET

    LAYOUT_SETTINGS = ModuleSettings(
        Path(__file__).parent / "bw_layout_graph_settings.json"
    )

    HOTKEY = "Hotkey"
    NODE_SPACING = "Node Spacing"
    MAINLINE_ADDITIONAL_OFFSET = "Mainline Settings;Additional Offset"
