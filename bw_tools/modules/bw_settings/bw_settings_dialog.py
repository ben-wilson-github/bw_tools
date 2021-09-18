import importlib
import json
import os
from pathlib import Path
from enum import Enum
from typing import Any, Dict, Optional, Tuple

from bw_tools.common import bw_ui_tools
from bw_tools.modules.bw_settings import bw_settings_model
from bw_tools.modules.bw_settings import settings_loader

from PySide2 import QtCore, QtGui, QtWidgets


class SettingsDialog(QtWidgets.QDialog):
    # value_updated = QtCore.Signal(Any)

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

        # self.value_updated.connect(self.on_value_updated)

        self._add_modules_to_model()
        self._create_module_widgets()
        self._create_ui()

        # Select first item in list
        index = self.module_model.index(0, 0)
        self.module_view_widget.selectionModel().setCurrentIndex(
            index, QtCore.QItemSelectionModel.SelectCurrent
        )
    
    def _create_module_widgets(self):
        for i in range(self.module_model.rowCount()):
            module_item = self.module_model.item(i, 0)
            module_name = module_item.text()

            module_widget = settings_loader.get_module_widget(module_item, self.module_model)
            self.module_settings_layout.addWidget(module_widget)

            self._module_setting_widgets[module_name] = module_widget

    def get_selected_module_item_from_model(
        self,
    ) -> Optional[QtGui.QStandardItem]:
        try:
            index = self.module_view_widget.selectedIndexes()[0]
        except IndexError:
            return None

        item = self.module_model.itemFromIndex(index)
        return item

    def get_model_item_from_value_widget(self, value_widget):
        def _find_setting_item(parent_item, setting_name):
            ret = None
            for row in range(parent_item.rowCount()):
                setting_item = parent_item.child(row)
                if setting_item.text() == setting_name:
                    return setting_item
                ret = _find_setting_item(setting_item, setting_name)
                if ret is not None:
                    break
            return ret

        # Get setting name from the value widget
        for i in range(self.module_settings_layout.count()):
            if self.module_settings_layout.itemAt(i).widget() is value_widget:
                setting_name = (
                    self.module_settings_layout.itemAt(i - 1).widget().text()
                )

        module_item = self.get_selected_module_item_from_model()
        return _find_setting_item(module_item, setting_name)

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

    def write_module_settings(self, module, file_path):
        """
        Writes the settings for the module to the given file path.
        @param module: QStandardItem
        @param file_path: Str
        """

        def _build_dict(parent_item, data):
            for row in range(parent_item.rowCount()):
                setting_item = parent_item.child(row)
                setting_name = setting_item.text()
                widget_type = self.get_widget_type(setting_item)
                value_item = self.get_child_item_with_key(
                    setting_item, "value"
                )
                value = value_item.data()

                data[setting_name] = {}

                if widget_type is WidgetTypes.GROUPBOX:
                    value = _build_dict(value_item, {})
                elif widget_type is WidgetTypes.COMBOBOX:
                    data[setting_name]["list"] = self.get_combobox_list(
                        setting_item
                    )
                else:
                    value = value_item.data()

                data[setting_name]["widget"] = widget_type.value
                data[setting_name]["value"] = value
            return data

        # Does not handle error or permission right now
        data = _build_dict(module, {})

        with open(file_path, "w") as settings_file:
            json.dump(data, settings_file, indent=4)

        self.api.logger.info(f"Writing settings for {module.text()}")

    def get_child_item_with_key(self, item, key):
        for i in range(item.rowCount()):
            if item.child(i).text() == key:
                return item.child(i)

    def get_value(self, item):
        return self.get_child_item_with_key(item, "value").data()

    def get_widget_type(self, item):
        return WidgetTypes(self.get_child_item_with_key(item, "widget").data())

    def get_combobox_list(self, item):
        return self.get_child_item_with_key(item, "list").data()

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
        for setting_name, value in settings.items():
            setting_item = QtGui.QStandardItem(setting_name)
            parent_item.appendRow(setting_item)

            if isinstance(value, dict):
                self._add_module_settings_to_model(setting_item, value)
                continue

            if isinstance(value, (list, tuple)):
                for v in value:
                    value_item = QtGui.QStandardItem(str(v))
                    value_item.setData(v)
                    setting_item.appendRow(value_item)
                continue

            value_item = QtGui.QStandardItem(str(value))
            value_item.setData(value)
            setting_item.appendRow(value_item)

    def on_value_updated(self):
        pass

    def on_str_value_changed(self):
        item = self.get_model_item_from_value_widget(self.sender())
        value_item = self.get_child_item_with_key(item, "value")
        value_item.setData(self.sender().text())

    def on_int_float_value_changed(self):
        item = self.get_model_item_from_value_widget(self.sender())
        value_item = self.get_child_item_with_key(item, "value")
        value_item.setData(self.sender().value())

    def on_bool_value_changed(self):
        item = self.get_model_item_from_value_widget(self.sender())
        value_item = self.get_child_item_with_key(item, "value")
        value_item.setData(self.sender().isChecked())

    def on_combobox_value_changed(self):
        item = self.get_model_item_from_value_widget(self.sender())
        value_item = self.get_child_item_with_key(item, "value")
        value_item.setData(self.sender().currentIndex())

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

        # settings_loader.clear_layout(self.module_settings_layout)

        # if isinstance(module.data(), FileNotFoundError):
        #     self.module_settings_layout.addWidget(
        #         QtWidgets.QLabel(str(module.data()))
        #     )
        #     return

        # for i in range(module.rowCount()):
        #     settings_loader.add_setting_to_layout(
        #         self.module_settings_layout, module.child(i), self.module_model
        #     )

    def on_clicked_apply(self):
        for row in range(self.module_model.rowCount()):
            item = self.module_model.item(row, 0)

            file_path = self.settings_file_dir.joinpath(
                f"{item.text()}/{item.text()}_settings.json"
            )

            self.write_module_settings(item, file_path)

    def on_clicked_ok(self):
        self.on_clicked_apply()
        self.close()

    def _create_ui(self):
        self._ui_frame_modules_list(0)
        self._ui_frame_module_settings(1)
        self._ui_frame_buttons(1)
        self._ui_frame_debug_model(2)

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
