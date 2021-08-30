import importlib
import logging
from typing import List, TypeVar

import sd
from bw_tools.common import bw_toolbar
from PySide2 import QtWidgets


# Types for type hinting
TYPE_MODULES = TypeVar("TYPE_MODULES")
SDContext = TypeVar("SDContext")
SDNode = TypeVar("SDNode")
SDSBSCompGraph = TypeVar("SDSBSCompGraph")
SDSBSCompNode = TypeVar("SDSBSCompNode")
SDProperty = TypeVar("SDProperty")
SDConnection = TypeVar("SDConnection")


class APITool:
    """
    Helper class to interface and pass various API related objects around.

    Modules are automatically loaded by creating a .py file inside a folder
    with the same name, inside the modules folder. For example
    bwTools/modules/my_module/my_module.py.

    Modules must contains .on_initialize(bw_api_tool.APITool) in order to
    loaded.

    The module is responsible for doing any setup code. Callbacks can be
    registered with the APITool.register_on_...().

    There are two toolbars available, the main top toolbar and a graph view
    toolbar. These can be accessed with .toolbar and .graph_view_toolbar
    respectively.

    Modules can have settings defined by creating a module_name.json file.
    The settings will automatically be added to the settings dialog.
    """

    def __init__(self, logger=None):
        self.context: SDContext = sd.getContext()
        if logger is None:
            logger = logging.getLogger("Root")
        self.logger: logging.RootLogger = logger
        self.application: sd.api.sdapplication.SDApplication = (
            self.context.getSDApplication()
        )
        self.ui_mgr: sd.api.sduimgr.SDUIMgr = (
            self.application.getQtForPythonUIMgr()
        )
        self.pkg_mgr: sd.api.sdpackagemgr.SDPackageMgr = (
            self.application.getPackageMgr()
        )
        self.main_window: QtWidgets.QMainWindow = self.ui_mgr.getMainWindow()
        self.loaded_modules: List[TYPE_MODULES] = []
        self.graph_view_toolbar: bw_toolbar.BWToolbar = None
        self.menu = None
        self.callback_ids: List[int] = []
        self.debug: bool = True

        self._menu_object_name = "bw_tools_menu_obj"
        self._menu_label = " BW Tools"

        self.logger.info(f"{self.__class__.__name__} initialized.")

    @property
    def current_selection(self) -> List[SDNode]:
        return self.ui_mgr.getCurrentGraphSelectedNodes()

    @property
    def current_graph(self) -> SDSBSCompGraph:
        return self.ui_mgr.getCurrentGraph()

    @property
    def log(self) -> logging.RootLogger:
        return self.logger

    def initialize(self, module: TYPE_MODULES) -> bool:
        """Initialize a module by calling the modules .on_initialize()"""
        if module.__name__ not in self.loaded_modules:
            if self.debug:
                importlib.reload(module)
                self.logger.debug(f"Reloaded module {module.__name__}.")

            try:
                self.logger.info(f"Initializing module {module.__name__}...")
                module.on_initialize(self)
            except AttributeError:
                self.logger.warning(
                    f"Unable to initialize module {module.__name__}, "
                    f"on_initialize() has not been implemented correctly."
                )
                return False
            else:
                name = module.__name__.split(".")[
                    -1
                ]  # Strips module path and returns the name
                self.loaded_modules.append(name)
                self.logger.info(f"Initialized module {name}.")
                return True

    def unload(self, module: TYPE_MODULES) -> bool:
        if module.__name__ not in self.loaded_modules:
            return False

        module.on_unload()
        self.loaded_modules.remove(module.__name__)

    def add_menu(self):
        self.logger.debug("Creating menu")
        self.menu = self.ui_mgr.newMenu(
            self._menu_label, self._menu_object_name
        )

    def remove_menu(self):
        self.ui_mgr.deleteMenu(self._menu_object_name)

    def add_toolbar_to_graph_view(self) -> bool:
        self.logger.info("Registering on graph view created callback")
        self.register_on_graph_view_created_callback(
            self._create_graph_view_toolbar
        )
        return True

    def unregister_callbacks(self):
        for callback in self.callback_ids:
            self.ui_mgr.unregisterCallback(callback)

    def register_on_graph_view_created_callback(self, func):
        self.callback_ids.append(
            self.ui_mgr.registerGraphViewCreatedCallback(func)
        )

    def _create_graph_view_toolbar(self, graph_view_id):
        toolbar = bw_toolbar.BWToolbar()
        self.ui_mgr.addToolbarToGraphView(
            graph_view_id, toolbar, icon=None, tooltip="BW Toolbar"
        )
        self.graph_view_toolbar = toolbar
