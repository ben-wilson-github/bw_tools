import importlib
import os
import sys
from pathlib import Path

# To resolve imports for the packaged plugin
# we must insert the root directory
ROOT_DIR = Path(__file__).parent
if not ROOT_DIR in sys.path:
    sys.path.insert(0, ROOT_DIR)

# Add windows specific because designer does not
# resolve / correctly
if not os.path.normpath(ROOT_DIR) in sys.path:
    sys.path.insert(0, os.path.normpath(ROOT_DIR))

for path in sys.path:
    print(path)


from bw_tools.common.bw_api_tool import BWAPITool

# TODO: Fix imports and generating of path
# TODO: Clean up every file
# TODO: Fix imports to relative where possible
# TODO: remove comment in node_selection._add_output_nodes after checking unit tests 

API_TOOL = BWAPITool()


def initializeSDPlugin():
    API_TOOL.initialize_logger()
    API_TOOL.add_menu()

    modules_dir = ROOT_DIR / "bw_tools/modules"
    for name in os.listdir(modules_dir):
        if not name.startswith("bw_"):
            continue

        try:
            module_path = f"bw_tools.modules.{name}.{name}"
            API_TOOL.logger.debug(f"Attempting to initialize {module_path}...")
            module = importlib.import_module(module_path)
        except ModuleNotFoundError:
            API_TOOL.logger.error(f"Failed to import module {module_path}")
            continue
        else:
            API_TOOL.initialize(module)


def uninitializeSDPlugin():
    API_TOOL.uninitialize_logger()
    API_TOOL.unregister_callbacks()
    API_TOOL.remove_toolbars()
    API_TOOL.remove_menu()
