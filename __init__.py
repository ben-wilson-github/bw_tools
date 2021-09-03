import importlib
import os
import sys
from pathlib import Path

# Add path to sys.path
ROOT_DIR = Path(__file__).parent
if not ROOT_DIR.resolve() in sys.path:
    sys.path.append(ROOT_DIR.resolve())

from bw_tools.common import bw_api_tool, bw_logging

# TODO: Cant have toolbar on graph switch, not loading with pixel processors. Need to use graph ID
# TODO: Is it possible to do frame plugin now?
# TODO: Make sure its clear you need PIL in install dir to run unittests
# TODO: integrate optimize graph module
# TODO: integrate PBR reference module
# TODO: Unit tests for all the settings
# TODO: default setting files
# TODO: reframe to selection plugin
# TODO: Add visual indents to settings frame
# TODO: Add sub comments to settings (requires restart)
# TODO: Test Threads for updating graph in real time?
# TODO: MOVE Type vars to api tool
# TODO: Icon for graph shelf

LOGGER = bw_logging.create_logger(ROOT_DIR / "bwtools.log")
API_TOOL = bw_api_tool.APITool(LOGGER["logger"])


def initializeSDPlugin():
    API_TOOL.add_menu()
    API_TOOL.add_toolbar_to_graph_view()

    modules_dir = ROOT_DIR / "bw_tools/modules"
    for name in os.listdir(modules_dir):
        try:
            module_path = f"bw_tools.modules.{name}.{name}"
            API_TOOL.logger.debug(f"Attempting to import {module_path}")
            module = importlib.import_module(module_path)
        except ModuleNotFoundError:
            API_TOOL.logger.debug("Failed...")
            continue
        else:
            API_TOOL.initialize(module)


def uninitializeSDPlugin():
    LOGGER["logger"].removeHandler(LOGGER["file_handler"])
    LOGGER["logger"].removeHandler(LOGGER["stream_handler"])
    API_TOOL.unregister_callbacks()
    API_TOOL.remove_menu()
