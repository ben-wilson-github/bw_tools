import importlib
import json
import os
from pathlib import Path
from enum import Enum

from bw_tools.common import bw_ui_tools
from bw_tools.modules.bw_settings import bw_settings_model
from .widgets import StringValueWidget, IntValueWidget, RGBAValueWidget
from PySide2 import QtCore, QtGui, QtWidgets


class WidgetTypes(Enum):
    GROUPBOX = 0
    LINEEDIT = 1
    SPINBOX = 2
    CHECKBOX = 3
    COMBOBOX = 4
    RGBA = 5


class SettingsDialog(QtWidgets.QDialog):
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
        self.module_settings_layout = QtWidgets.QGridLayout()
        self.settings_file_dir = Path(__file__).parent / ".."

        self._create_ui()
        self.add_modules_to_model()

        # Select first item in list
        index = self.module_model.index(0, 0)
        self.module_view_widget.selectionModel().setCurrentIndex(
            index, QtCore.QItemSelectionModel.SelectCurrent
        )

    def get_selected_module_item_from_model(self):
        """
        @return: QStandardItem
        """
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

    def get_settings_for_module(self, file_path):
        """
        Returns the setting read from given file path.
        Returns FileNotFoundError is there was an issue reading the .json
        @param file_path: Str
        @return: Dict() || FileNotFoundError
        """

        if not os.path.isfile(file_path):
            raise FileNotFoundError("This module has no settings.")

        try:
            with open(file_path) as settings_file:
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

    def add_item_to_settings_frame(self, item, row):
        setting_name = item.text()
        widget_type = self.get_widget_type(item)
        value = self.get_value(item)

        func = None
        if widget_type is WidgetTypes.GROUPBOX:
            row = self._ui_add_group_label_to_settings_frame(setting_name, row)
            value_item = self.get_child_item_with_key(item, "value")
            for i in range(value_item.rowCount()):
                row = self.add_item_to_settings_frame(value_item.child(i), row)

        elif widget_type is WidgetTypes.LINEEDIT:
            self.module_settings_layout.addWidget(
                    StringValueWidget(setting_name, value)
                )

        elif widget_type is WidgetTypes.SPINBOX:
            if isinstance(value, float):
                func = self._ui_add_float_value_to_settings_frame
            else:
                self.module_settings_layout.addWidget(
                    IntValueWidget(setting_name, value)
                )

        elif widget_type is WidgetTypes.CHECKBOX:
            func = self._ui_add_bool_value_to_settings_frame

        elif widget_type is WidgetTypes.COMBOBOX:
            row = self._ui_add_combobox_value_to_settings_frame(
                setting_name, value, self.get_combobox_list(item), row
            )
        elif widget_type is WidgetTypes.RGBA:
            self.module_settings_layout.addWidget(
                RGBAValueWidget(setting_name, tuple(value)), row, 0
            )

        if func:
            row = func(setting_name, value, row)

        return row + 1

    def clear_settings_frame(self):
        def _delete_children(layout):
            for i in reversed(range(layout.count())):
                item = layout.itemAt(i)
                if isinstance(
                    item,
                    (
                        QtWidgets.QGridLayout,
                        QtWidgets.QHBoxLayout,
                        QtWidgets.QVBoxLayout,
                    ),
                ):
                    _delete_children(item)
                else:
                    widget = item.widget()
                    widget.deleteLater()

        _delete_children(self.module_settings_layout)

    def add_modules_to_model(self):
        self.module_model.clear()

        for row, module in enumerate(self.api.loaded_modules):
            module_item = QtGui.QStandardItem(module)
            self.module_model.setItem(row, 0, module_item)

            try:
                file_path = self.settings_file_dir.joinpath(
                    f"{module}/{module}_settings.json"
                )
                settings = self.get_settings_for_module(
                    str(file_path.resolve())
                )
            except FileNotFoundError as e:
                self.api.logger.warning(str(e))
                module_item.setData(e)
            else:
                self.add_settings_to_model_item(
                    module_item, settings
                )  # Must take in settings, as setting data will reorder

    def add_settings_to_model_item(self, parent_item, settings):
        """
        @param parent_item: QtStandardItem
        @param settings: dict()
        """
        for name, value in settings.items():
            item = QtGui.QStandardItem(name)
            parent_item.appendRow(item)
            if isinstance(value, dict):
                self.add_settings_to_model_item(item, value)
            else:
                item.setData(value)

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
        self.clear_settings_frame()

        module = self.get_selected_module_item_from_model()
        if module is None:
            return

        if self.api.debug:
            self.api.logger.debug(
                f"User clicked on {module.text()} inside settings dialog."
            )

        if isinstance(module.data(), FileNotFoundError):
            self.module_settings_layout.addWidget(
                QtWidgets.QLabel(str(module.data()))
            )
        else:
            row = 0
            for i in range(module.rowCount()):
                row = self.add_item_to_settings_frame(module.child(i), row)

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

    def _ui_add_group_label_to_settings_frame(self, name, row=0):
        self.module_settings_layout.addWidget(
            bw_ui_tools.label(name, alignment=QtCore.Qt.AlignLeft),
            row,
            0,
            1,
            2,
        )
        return row + 1

    def _ui_add_settings_to_settings_frame(self, settings, row=0):
        """
        Recursively popuplate the settings frame with appropiate widgets based
        on the value type
        @param settings: A dictionary read from a json file
        @param row: The row
        @return: The new row after all recursive calls
        """
        for key, value in settings.items():
            if isinstance(value, dict):
                for _ in range(4):
                    self.module_settings_layout.addWidget(
                        bw_ui_tools.separator_frame(), row, 0, 1, 2
                    )
                    row += 1
                self.module_settings_layout.addWidget(
                    bw_ui_tools.separator(), row, 0, 1, 2
                )
                self.module_settings_layout.addWidget(
                    bw_ui_tools.label(key, alignment=QtCore.Qt.AlignLeft),
                    row + 1,
                    0,
                    1,
                    2,
                )
                row = self._ui_add_settings_to_settings_frame(value, row + 2)
            elif isinstance(value, str):
                self._ui_add_string_value_to_settings_frame(key, value, row)
            elif isinstance(value, bool):
                self._ui_add_bool_value_to_settings_frame(key, value, row)
            elif isinstance(value, int):
                self._ui_add_int_value_to_settings_frame(key, value, row)
            elif isinstance(value, float):
                self._ui_add_float_value_to_settings_frame(key, value, row)
            elif isinstance(value, list):
                self._ui_add_list_value_to_settings_frame(key, value, row)
            else:
                self.module_settings_layout.addWidget(
                    bw_ui_tools.label("Unsupported type.")
                )
            row += 1
        return row

    def _ui_add_list_value_to_settings_frame(self, name, value, row):
        self._ui_add_value_name_to_settings_frame(name, row)
        if not all(
            isinstance(elem, (str, bool, int, float)) for elem in value
        ):
            self.module_settings_layout.addWidget(
                QtWidgets.QLabel(
                    "Only str, bool, int, float are supported values!"
                ),
                row,
                1,
            )
            return row + 1

        string = ""
        for item in value:
            string += f"{str(item)};"
        w = QtWidgets.QLineEdit(string)
        w.textChanged.connect(self.on_str_value_changed)
        w.setStyleSheet(f"background : {self._value_background}")
        w.setAlignment(QtCore.Qt.AlignRight)
        self.module_settings_layout.addWidget(w, row, 1)
        return row + 1

    def _ui_add_float_value_to_settings_frame(self, name, value, row):
        self._ui_add_value_name_to_settings_frame(name, row)
        w = QtWidgets.QDoubleSpinBox()
        w.setMaximum(99999.0)
        w.setValue(value)
        w.setSingleStep(0.01)
        w.valueChanged.connect(self.on_int_float_value_changed)
        w.setStyleSheet(
            "QDoubleSpinBox"
            "{"
            f"background : {self._value_background};"
            "color : #cccccc;"
            "}"
        )
        w.setAlignment(QtCore.Qt.AlignRight)
        self.module_settings_layout.addWidget(w, row, 1)
        return row + 1

    def _ui_add_bool_value_to_settings_frame(self, name, value, row):
        self._ui_add_value_name_to_settings_frame(name, row)
        w = QtWidgets.QCheckBox()
        w.setChecked(value)
        w.stateChanged.connect(self.on_bool_value_changed)
        self.module_settings_layout.addWidget(
            w, row, 1, 1, 1, QtCore.Qt.AlignRight
        )
        return row + 1

    def _ui_add_combobox_value_to_settings_frame(
        self, name, value, item_list, row
    ):
        self._ui_add_value_name_to_settings_frame(name, row)

        combo = QtWidgets.QComboBox()
        self.module_settings_layout.addWidget(combo, row, 1)
        combo.addItems(item_list)
        combo.setCurrentIndex(value)
        combo.currentIndexChanged.connect(self.on_combobox_value_changed)
        return row + 1

    def _ui_add_value_name_to_settings_frame(self, name, row):
        w = QtWidgets.QLabel(name)
        self.module_settings_layout.addWidget(w, row, 0)
        return row + 1
