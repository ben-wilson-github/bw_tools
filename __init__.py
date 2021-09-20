import importlib
import os
import sys
from pathlib import Path

# Add path to sys.path
ROOT_DIR = Path(__file__).parent
if not ROOT_DIR.resolve() in sys.path:
    sys.path.append(ROOT_DIR.resolve())

from bw_tools.common import bw_api_tool, bw_logging

# TODO: Strip out logging
# TODO: Clean up every file

LOGGER = bw_logging.create_logger(ROOT_DIR / "bwtools.log")
API_TOOL = bw_api_tool.APITool(LOGGER["logger"])


def initializeSDPlugin():
    API_TOOL.add_menu()

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
    API_TOOL.remove_toolbars()
    API_TOOL.remove_menu()
