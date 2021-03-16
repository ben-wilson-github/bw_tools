import sd
import os
import logging
import importlib
import inspect
from dataclasses import dataclass, field
from typing import List
from typing import TypeVar
from common import bw_toolbar
from common import bw_utils
from PySide2 import QtWidgets
from PySide2 import QtCore

importlib.reload(bw_toolbar)
importlib.reload(bw_utils)

# Types for type hinting
TYPE_MODULES = TypeVar('modules')
SDNode = TypeVar('SDNode')
SDSBSCompGraph = TypeVar('SDSBSCompGraph')


@dataclass()
class APITool:
    """
    Helper class to interface and pass various API related objects around.

    Modules are automatically loaded by creating a .py file inside a folder with
    the same name, inside the modules folder. For example
    bwTools/modules/my_module/my_module.py.

    Modules must contains .on_initialize(bw_api_tool.APITool) in order to loaded.

    The module is responsible for doing any setup code. Callbacks can be registered
    with the APITool.register_on_...().

    There are two toolbars available, the main top toolbar and a graph view toolbar.
    These can be accessed with .toolbar and .graph_view_toolbar respectively.

    Modules can have settings defined by creating a module_name.json file.
    The settings will automatically be added to the settings dialog.
    """
    context: sd.context.Context
    logger: logging.RootLogger

    application: sd.api.sdapplication.SDApplication = field(init=False)
    ui_mgr: sd.api.sduimgr.SDUIMgr = field(init=False)
    pkg_mgr: sd.api.sdpackagemgr.SDPackageMgr = field(init=False)
    main_window: QtWidgets.QMainWindow = field(init=False)
    loaded_modules: List[TYPE_MODULES] = field(init=False, default_factory=list)
    toolbar: bw_toolbar.BWToolbar = field(init=False, default=None)
    graph_view_toolbar: bw_toolbar.BWToolbar = field(init=False, default=None)
    debug: bool = field(init=False, default=True)
    callback_ids: List[int] = field(init=False, default_factory=list)

    def __post_init__(self):
        object.__setattr__(self, 'application', self.context.getSDApplication())
        object.__setattr__(self, 'ui_mgr', self.application.getQtForPythonUIMgr())
        object.__setattr__(self, 'pkg_mgr', self.application.getPackageMgr())
        object.__setattr__(self, 'main_window', self.ui_mgr.getMainWindow())

        if type(self.context) != self.__dataclass_fields__['context'].type \
                or type(self.logger) != self.__dataclass_fields__['logger'].type:
            raise TypeError(bw_utils.type_error_message(self.__init__, self.context, self.logger))

        self.logger.info(f'{self.__class__.__name__} initialized.')

    @property
    def current_selection(self) -> List[SDNode]:
        return self.ui_mgr.getCurrentGraphSelection()

    @property
    def current_graph(self) -> SDSBSCompGraph:
        return self.ui_mgr.getCurrentGraph()

    def initialize(self, module: TYPE_MODULES) -> bool:
        """Initialize a module by calling the modules .on_initialize()"""
        if not inspect.ismodule(module):
            raise TypeError(bw_utils.type_error_message(self.initialize, module))

        if module.__name__ not in self.loaded_modules:
            if self.debug:
                importlib.reload(module)
                self.logger.debug(f'Reloaded module {module.__name__}.')

            try:
                self.logger.info(f'Initializing module {module.__name__}...')
                module.on_initialize(self)
            except AttributeError:
                self.logger.warning(
                    f'Unable to initialize module {module.__name__}, '
                    f'on_initialize() has not been implemented correctly.'
                )
                return False
            else:
                name = module.__name__.split('.')[-1]   # Strips module path and returns the name
                self.loaded_modules.append(name)
                self.logger.info(f'Initialized module {name}.')
                return True

    def unload(self, module: TYPE_MODULES) -> bool:
        if module.__name__ not in self.loaded_modules:
            return False

        module.on_unload()
        self.loaded_modules.remove(module.__name__)

    def add_top_toolbar(self) -> bool:
        self.logger.info('Creating top toolbar...')
        self.toolbar = bw_toolbar.BWToolbar(self.main_window)
        self.main_window.addToolBar(QtCore.Qt.TopToolBarArea, self.toolbar)
        return True

    def add_toolbar_to_graph_view(self) -> bool:
        self.register_on_graph_view_created_callback(
            self._create_graph_view_toolbar
        )
        return True

    def unregister_callbacks(self):
        for callback in self.callback_ids:
            self.ui_mgr.unregisterCallback(callback)

    def find_all_toolbars(self) -> List[bw_toolbar.BWToolbar]:
        ret = []
        toolbars = self.main_window.findChildren(QtWidgets.QToolBar)
        for toolbar in toolbars:
            if toolbar.__class__.__name__ == self.toolbar.uid:
                ret.append(toolbar)
        return ret

    def register_on_graph_view_created_callback(self, func):
        self.callback_ids.append(
            self.ui_mgr.registerGraphViewCreatedCallback(func)
        )

    def _create_graph_view_toolbar(self, graph_view_id):
        toolbar = bw_toolbar.BWToolbar()
        self.ui_mgr.addToolbarToGraphView(
            graph_view_id,
            toolbar,
            icon=None,
            tooltip='BW Toolbar'
        )
        self.graph_view_toolbar = toolbar