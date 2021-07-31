# import importlib
# from PySide2 import QtWidgets
# from abc import ABC, abstractmethod
# from dataclasses import dataclass
#
# from common import bw_api_tool, bw_utils
# importlib.reload(bw_api_tool)
# importlib.reload(bw_utils)
#
#
# class AbstractModule(ABC):
#     def __init__(self, api_tool):
#         err_msg = f'Unable to initialize {type(self)}. ' \
#                   f'Wrong argument passed in, supported signatures are: ' \
#                   f'{bw_api_tool.APITool}'
#         # isinstance doesnt work for some reason??
#         # if not isinstance(api_tool, bw_api_tool.APITool):
#         if not self._isinstance(api_tool, bw_api_tool.APITool):    # Use custom check instead
#             raise TypeError(err_msg)
#
#         self._api_tool = api_tool
#
#     @property
#     def name(self):
#         return self.__class__.__name__
#
#     @property
#     def api_tool(self):
#         return self._api_tool
#
#     @abstractmethod
#     def on_module_load(self):
#         pass
#
#     @abstractmethod
#     def on_module_unload(self):
#         pass
#
#     def settings(self):
#         return None
#
#     @staticmethod
#     def _isinstance(a, b):
#         if str(type(a)) == str(b):
#             return True
#         return False
#
#
# class AbstractToolBarModule(AbstractModule):
#     def __init__(self, api_tool, toolbar):
#         err_msg = f'Unable to initialize {type(self)}. ' \
#                 f'Supported signatures are:' \
#                 f'{bw_api_tool.APITool, QtWidgets.QToolBar}'
#         if not self._isinstance(api_tool, bw_api_tool.APITool) or not isinstance(toolbar, QtWidgets.QToolBar):
#             raise TypeError(err_msg)
#
#         super().__init__(api_tool=api_tool)
#
#         self.toolbar = toolbar
