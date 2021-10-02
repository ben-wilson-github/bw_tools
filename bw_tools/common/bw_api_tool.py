import json
import logging
from enum import Enum
from pathlib import Path
from typing import List, Optional, TypeVar

import sd
from PySide2 import QtGui, QtWidgets
from sd.api.qtforpythonuimgrwrapper import QtForPythonUIMgrWrapper
from sd.api.sbs.sdsbscompgraph import SDSBSCompGraph
from sd.api.sbs.sdsbsfunctiongraph import SDSBSFunctionGraph
from sd.api.sdapplication import SDApplication
from sd.api.sdgraph import SDGraph
from sd.api.sdgraphobject import SDGraphObject
from sd.api.sdnode import SDNode
from sd.api.sdpackage import SDPackage
from sd.api.sdpackagemgr import SDPackageMgr
from sd.context import Context as SDContext

from .bw_toolbar import BWToolbar

BW_MODULE = TypeVar("BW_MODULE")


class CompNodeID(Enum):
    DOT = "sbs::compositing::passthrough"
    UNIFORM_COLOR = "sbs::compositing::uniform"
    COMP_GRAPH = "sbs::compositing::sbscompgraph_instance"
    OUTPUT = "sbs::compositing::output"


class FunctionNodeId(Enum):
    DOT = "sbs::function::passthrough"


class BWAPITool:
    """
    Helper class to interface and pass various API related objects around.

    Modules are automatically loaded by creating a .py file inside a folder
    with the same name, inside the modules folder. For example
    bwTools/modules/my_module/my_module.py.

    Modules must contains .on_initialize(bw_api_tool.APITool) in order to
    loaded.

    The module is responsible for doing any setup code. Callbacks can be
    registered with the APITool.register_on_graph_view_created_callback()

    There are two toolbars available, the main top toolbar and a graph view
    toolbar. These can be accessed with .toolbar and .graph_view_toolbar
    respectively.

    Modules can have settings defined by creating a module_name.json file.
    The settings will automatically be added to the settings dialog.
    """

    def __init__(self):
        self.context: SDContext = sd.getContext()

        self.logger: Optional[logging.RootLogger] = None
        self.log_handler: Optional[logging.Handler] = None
        self.application: SDApplication = self.context.getSDApplication()
        self.ui_mgr: QtForPythonUIMgrWrapper = (
            self.application.getQtForPythonUIMgr()
        )
        self.pkg_mgr: SDPackageMgr = self.application.getPackageMgr()
        self.main_window: QtWidgets.QMainWindow = self.ui_mgr.getMainWindow()
        self.loaded_modules: List[BW_MODULE] = []
        self.menu: Optional[QtWidgets.QMenu] = None
        self.callback_ids: List[int] = []

        self.graph_view_toolbar: Optional[BWToolbar] = None
        self._graph_view_toolbar_list: dict[int, BWToolbar] = dict()
        self._menu_object_name = "bw_tools_menu_obj"
        self._menu_label = " BW Tools"

    @property
    def current_node_selection(self) -> List[SDNode]:
        return self.ui_mgr.getCurrentGraphSelectedNodes()

    @property
    def current_graph(self) -> SDGraph:
        return self.ui_mgr.getCurrentGraph()

    @property
    def current_package(self) -> SDPackage:
        return self.current_graph.getPackage()

    @property
    def current_graph_object_selection(self) -> List[SDGraphObject]:
        return self.ui_mgr.getCurrentGraphSelectedObjects()

    @property
    def current_graph_is_supported(self) -> bool:
        """
        Returns whether the graph is a support type for bw_tools.

        Some graph types in the designer API are not fully supported.
        We only support those which are fully functional.

        This property should be removed when the API is updated.
        """
        # Some graphs do not even return with the designer API
        if self.current_graph is None:
            return False

        return isinstance(
            self.current_graph, (SDSBSCompGraph, SDSBSFunctionGraph)
        )

    @property
    def log(self) -> logging.RootLogger:
        return self.logger

    def get_graph_view_toolbar(self, graph_view_id: int) -> BWToolbar:
        try:
            toolbar = self._graph_view_toolbar_list[graph_view_id]
        except KeyError:
            return None
        else:
            return toolbar

    def initialize_logger(self):
        self.logger = logging.getLogger("bw_tools")
        self.log_handler = sd.getContext().createRuntimeLogHandler()
        self.logger.propagate = False
        self.logger.addHandler(self.log_handler)
        self.logger.setLevel(logging.DEBUG)

    def uninitialize_logger(self):
        self.logger.removeHandler(self.log_handler)
        self.log_handler = None

    def initialize(self, module: BW_MODULE) -> bool:
        """Initialize a module by calling the modules .on_initialize()"""
        if module.__name__ not in self.loaded_modules:
            try:
                module.on_initialize(self)
            except AttributeError:
                self.logger.warning(
                    f"Unable to initialize module {module.__name__}, "
                    f"on_initialize() has not been implemented correctly"
                )
                return False

            name = module.__name__.split(".")[
                -1
            ]  # Strips module path and returns the name
            self.loaded_modules.append(name)
            self.logger.info(f"Initialized module {name}")

            try:
                default_settings = module.get_default_settings()
            except AttributeError:
                pass
            else:
                module_settings = Path(__file__).parent.joinpath(
                    "..",
                    "modules",
                    name,
                    f"{name}_settings.json",
                )
                if not module_settings.exists():
                    self.logger.info(
                        f"Missing settings file for {name}. " "Writing new one"
                    )
                    with open(
                        str(module_settings.resolve()), "w"
                    ) as settings_file:
                        json.dump(default_settings, settings_file, indent=4)

            return True

    def unload(self, module: BW_MODULE) -> bool:
        if module.__name__ not in self.loaded_modules:
            return False

        module.on_unload()
        self.loaded_modules.remove(module.__name__)

    def add_menu(self):
        self.logger.debug("Creating BW Tools menu...")
        self.menu = self.ui_mgr.newMenu(
            self._menu_label, self._menu_object_name
        )

    def remove_menu(self):
        self.ui_mgr.deleteMenu(self._menu_object_name)

    def unregister_callbacks(self):
        for callback in self.callback_ids:
            self.ui_mgr.unregisterCallback(callback)

    def register_on_graph_view_created_callback(self, func) -> int:
        graph_view_id = self.ui_mgr.registerGraphViewCreatedCallback(func)
        self.callback_ids.append(graph_view_id)
        return graph_view_id

    def add_toolbar_to_graph_view(self, graph_view_id: int):
        if self.graph_view_toolbar is None:
            self.graph_view_toolbar = BWToolbar(self.main_window)

        icon = Path(__file__).parent / "resources/bw_tools_icon.png"
        self.ui_mgr.addToolbarToGraphView(
            graph_view_id,
            self.graph_view_toolbar,
            icon=QtGui.QIcon(str(icon.resolve())),
            tooltip="BW Toolbar",
        )

    def remove_toolbars(self):
        for toolbar in self._graph_view_toolbar_list.values():
            toolbar.deleteLater()
