import importlib
import os
import sys
from pathlib import Path

# To resolve imports for the packaged plugin
# we must insert the root directory
ROOT_DIR = Path(__file__).parent
if ROOT_DIR not in sys.path:
    sys.path.insert(0, str(ROOT_DIR.resolve()))

# Add windows specific because designer does not
# resolve / correctly
if os.path.normpath(ROOT_DIR) not in sys.path:
    sys.path.insert(0, os.path.normpath(ROOT_DIR))


from bw_tools.common.bw_api_tool import BWAPITool


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
