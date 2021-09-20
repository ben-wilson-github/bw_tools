import importlib
import json
import os
from pathlib import Path
from enum import Enum
from typing import Any, Dict, Optional, Tuple

from bw_tools.common import bw_ui_tools
from bw_tools.modules.bw_settings import bw_settings_model
from bw_tools.modules.bw_settings import settings_loader, setting_writer

from PySide2 import QtCore, QtGui, QtWidgets


class SettingsDialog(QtWidgets.QDialog):
    """
    Popup dialog containing settings for all modules present.

    Settings are dynamically built upon finding a <module_name_settings.json>
    file. See settings_loader.py for documentation on the format for a
    settings file.

    The dialog uses a model which directly correllates to the settings file, 
    where each QStandardItem.text() contains the str representation of every
    value and the actual value in QStandardItem.data().
    """
    def __init__(self, api):
        super(SettingsDialog, self).__init__(parent=api.main_window)
        self._value_background = "#151515"

        self.setModal(False)
        self.api = api
        self.main_layout = QtWidgets.QGridLayout()
        self.setLayout(self.main_layout)
        self.module_model = bw_settings_model.ModuleModel()
        self.module_view_widget = QtWidgets.QListView()
        self.module_view_widget.setModel(self.module_model)
        self.module_settings_layout = QtWidgets.QVBoxLayout()
        self.settings_file_dir = Path(__file__).parent / ".."

        self._module_setting_widgets: dict[str, QtWidgets.QWidget] = {}

        self._add_modules_to_model()
        self._create_module_setting_widgets()
        self._create_ui()

        # Select first item in list
        index = self.module_model.index(0, 0)
        self.module_view_widget.selectionModel().setCurrentIndex(
            index, QtCore.QItemSelectionModel.SelectCurrent
        )

    def get_selected_module_item_from_model(
        self,
    ) -> Optional[QtGui.QStandardItem]:
        try:
            index = self.module_view_widget.selectedIndexes()[0]
        except IndexError:
            return None

        item = self.module_model.itemFromIndex(index)
        return item

    def get_settings_for_module(self, file_path: Path) -> Dict:
        """
        Returns the setting read from given file path.
        Returns FileNotFoundError is there was an issue reading the .json
        @param file_path: Str
        @return: Dict() || FileNotFoundError
        """
        if not file_path.is_file():
            raise FileNotFoundError("This module has no settings.")

        try:
            with open(str(file_path.resolve())) as settings_file:
                data = json.load(settings_file)
        except json.JSONDecodeError:
            raise FileNotFoundError(
                "Unable to load settings. Settings file is invalid."
            )
        else:
            return data

    def get_child_item_with_key(self, item, key):
        for i in range(item.rowCount()):
            if item.child(i).text() == key:
                return item.child(i)

    def get_widget_type(self, item):
        return WidgetTypes(self.get_child_item_with_key(item, "widget").data())

    def get_combobox_list(self, item):
        return self.get_child_item_with_key(item, "list").data()

    def on_clicked_module(self):
        module = self.get_selected_module_item_from_model()
        if module is None:
            return
        module_name = module.text()
        for name, widget in self._module_setting_widgets.items():
            if module_name == name:
                widget.show()
            else:
                widget.hide()

    def on_clicked_apply(self):
        for row in range(self.module_model.rowCount()):
            module_item = self.module_model.item(row, 0)

            settings_file_path: Path = (
                self.settings_file_dir
                / module_item.text()
                / f"{module_item.text()}_settings.json"
            )
            if not settings_file_path.exists():
                continue

            setting_writer.write_module_settings(
                module_item, settings_file_path
            )

    def on_clicked_ok(self):
        self.on_clicked_apply()
        self.close()

    def _add_modules_to_model(self):
        self.module_model.clear()

        for row, module in enumerate(self.api.loaded_modules):
            module_item = QtGui.QStandardItem(module)
            self.module_model.setItem(row, 0, module_item)

            try:
                settings = self.get_settings_for_module(
                    self.settings_file_dir / module / f"{module}_settings.json"
                )
            except FileNotFoundError as e:
                module_item.setData(e)
            else:
                self._add_module_settings_to_model(
                    module_item, settings
                )  # Must take in settings, as setting data will reorder

    def _add_module_settings_to_model(
        self, parent_item: QtGui.QStandardItem, settings: Dict
    ):
        for setting_name, setting_params in settings.items():
            setting_item = QtGui.QStandardItem(setting_name)
            parent_item.appendRow(setting_item)

            try:
                widget_type = setting_params["widget"]
            except KeyError:
                widget_type = None
            else:
                widget_param_item = QtGui.QStandardItem("widget")
                setting_item.appendRow(widget_param_item)

                widget_type_item = QtGui.QStandardItem(str(widget_type))
                widget_type_item.setData(widget_type)
                widget_param_item.appendRow(widget_type_item)

            try:
                possible_values = setting_params["list"]
            except KeyError:
                possible_values = None
            else:
                list_param_item = QtGui.QStandardItem("list")
                setting_item.appendRow(list_param_item)

                for v in possible_values:
                    item = QtGui.QStandardItem(str(v))
                    item.setData(v)
                    list_param_item.appendRow(item)

            try:
                value = setting_params["value"]
            except KeyError:
                value = None
            else:
                value_param_item = QtGui.QStandardItem("value")
                setting_item.appendRow(value_param_item)

                if isinstance(value, (list, tuple)):
                    for v in value:
                        item = QtGui.QStandardItem(str(v))
                        item.setData(v)
                        value_param_item.appendRow(item)
                else:
                    item = QtGui.QStandardItem(str(value))
                    item.setData(value)
                    value_param_item.appendRow(item)

            try:
                content = setting_params["content"]
            except KeyError:
                continue
            else:
                content_param_item = QtGui.QStandardItem("content")
                setting_item.appendRow(content_param_item)
                self._add_module_settings_to_model(content_param_item, content)

    def _create_module_setting_widgets(self):
        for i in range(self.module_model.rowCount()):
            module_item = self.module_model.item(i, 0)
            module_name = module_item.text()

            module_widget = settings_loader.get_module_widget(
                module_item, self.module_model
            )
            self.module_settings_layout.addWidget(module_widget)

            self._module_setting_widgets[module_name] = module_widget

    def _create_ui(self):
        self._ui_frame_modules_list(0)
        self._ui_frame_module_settings(1)
        self._ui_frame_buttons(1)
        # self._ui_frame_debug_model(2)

    def _ui_frame_debug_model(self, col):
        tree_view = QtWidgets.QTreeView()
        tree_view.setModel(self.module_model)
        self.main_layout.addWidget(tree_view, 1, col)

    def _ui_frame_modules_list(self, col):
        self.main_layout.addWidget(bw_ui_tools.label("Loaded Modules"), 0, col)
        self._ui_add_module_view_widget(col)

    def _ui_frame_module_settings(self, col):
        self.main_layout.addWidget(
            bw_ui_tools.label("Module Settings"), 0, col
        )
        scroll_area = self._ui_add_scroll_area_widget(col)
        self._ui_add_settings_widget(scroll_area)

    def _ui_frame_buttons(self, col):
        layout = QtWidgets.QHBoxLayout()
        self.main_layout.addLayout(layout, 2, col)

        layout.addStretch()

        w = QtWidgets.QPushButton("Ok")
        layout.addWidget(w)
        w.clicked.connect(self.on_clicked_ok)

        w = QtWidgets.QPushButton("Cancel")
        w.clicked.connect(self.close)
        layout.addWidget(w)

        w = QtWidgets.QPushButton("Apply")
        w.clicked.connect(self.on_clicked_apply)
        layout.addWidget(w)

    def _ui_add_module_view_widget(self, col):
        self.module_view_widget.setFixedWidth(130)
        self.module_view_widget.setEditTriggers(
            QtWidgets.QAbstractItemView.NoEditTriggers
        )
        self.main_layout.addWidget(self.module_view_widget, 1, col)
        self.module_view_widget.selectionModel().selectionChanged.connect(
            self.on_clicked_module
        )

    def _ui_add_settings_widget(self, scroll_area):
        settings_widget = QtWidgets.QWidget(scroll_area)
        settings_widget.setStyleSheet(
            """
            background : #252525;
            border-radius : 7px;
            """
        )
        scroll_area.setWidget(settings_widget)

        settings_widget_layout = QtWidgets.QVBoxLayout(settings_widget)
        settings_widget_layout.addLayout(self.module_settings_layout)
        settings_widget_layout.addStretch()

    def _ui_add_scroll_area_widget(self, col):
        scroll_area = QtWidgets.QScrollArea(self)
        scroll_area.setWidgetResizable(True)
        scroll_area.setMinimumSize(300, 300)
        self.main_layout.addWidget(scroll_area, 1, col)
        return scroll_area
