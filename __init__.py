import sd
import os
import sys
import importlib

from common import bw_logging
from common import bw_api_tool

importlib.reload(bw_logging)
importlib.reload(bw_api_tool)

# Add path to sys.path
if not os.path.realpath(os.path.dirname(__file__)) in sys.path:
    sys.path.append(os.path.realpath(os.path.dirname(__file__)))


LOGGER = bw_logging.create_logger(f'{os.path.dirname(__file__)}\\bwtools.log')
API_TOOL = bw_api_tool.APITool(LOGGER['logger'])


def initializeSDPlugin():
    API_TOOL.add_top_toolbar()
    API_TOOL.add_toolbar_to_graph_view()

    modules_dir = f'{os.path.dirname(__file__)}\\modules'
    for name in os.listdir(modules_dir):
        try:
            module = importlib.import_module(f'.{name}', f'modules.{name}')
        except ModuleNotFoundError:
            continue
        else:
            API_TOOL.initialize(module)


def uninitializeSDPlugin():
    LOGGER['logger'].removeHandler(LOGGER['file_handler'])
    LOGGER['logger'].removeHandler(LOGGER['stream_handler'])
    API_TOOL.unregister_callbacks()
    API_TOOL.remove_toolbars()

