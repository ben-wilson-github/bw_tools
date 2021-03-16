import importlib
import os
import json
from PySide2 import QtWidgets
from PySide2 import QtGui
from PySide2 import QtCore
from common import bw_ui_tools
from modules.bw_settings import bw_settings_model

importlib.reload(bw_ui_tools)
importlib.reload(bw_settings_model)


class SettingsDialog(QtWidgets.QDialog):
    def __init__(self, api):
        super(SettingsDialog, self).__init__(parent=api.main_window)
        self._value_background = '#151515'

        self.setModal(False)
        self.api = api
        self.main_layout = QtWidgets.QGridLayout()
        self.setLayout(self.main_layout)
        self.module_model = bw_settings_model.ModuleModel()
        self.module_view_widget = QtWidgets.QListView()
        self.module_view_widget.setModel(self.module_model)
        self.module_settings_layout = QtWidgets.QGridLayout()
        self.settings_file_dir = os.path.normpath(
            f'{os.path.dirname(__file__)}\\..'
        )

        self._create_ui()
        self.add_modules_to_model()

        # Select first item in list
        index = self.module_model.index(0, 0)
        self.module_view_widget.selectionModel().setCurrentIndex(
            index,
            QtCore.QItemSelectionModel.SelectCurrent
        )

    def get_selected_module_from_model(self):
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
                else:
                    if setting_item.hasChildren():
                        ret = _find_setting_item(setting_item, setting_name)
                        if ret is not None:
                            break
            return ret

        for i in range(self.module_settings_layout.count()):
            if self.module_settings_layout.itemAt(i).widget() is value_widget:
                setting_name = self.module_settings_layout.itemAt(i - 1).widget().text()

        module_item = self.get_selected_module_from_model()
        return _find_setting_item(module_item, setting_name)

    def get_settings_for_module(self, file_path):
        """
        Returns the setting read from given file path.
        Returns FileNotFoundError is there was an issue reading the .json
        @param file_path: Str
        @return: Dict() || FileNotFoundError
        """

        if not os.path.isfile(file_path):
            raise FileNotFoundError('This module has no settings.')

        try:
            with open(file_path) as settings_file:
                data = json.load(settings_file)
        except json.JSONDecodeError:
            raise FileNotFoundError(f'Unable to load settings. Settings file is invalid.')
        else:
            return data

    def write_module_settings(self, module, file_path):
        """
        Writes the settings for the module to the given file path.
        @param module: QStandardItem
        @param file_path: Str
        """
        def _build_dict(parent_item, return_dict):
            for row in range(parent_item.rowCount()):
                item = parent_item.child(row)

                if item.data() is None:
                    data = _build_dict(item, return_dict={})
                else:
                    data = item.data()

                return_dict[item.text()] = data
            return return_dict

        new_settings = _build_dict(module, dict())

        # Does not handle error or permission right now
        with open(file_path, 'w') as settings_file:
            json.dump(new_settings, settings_file, indent=4)

        self.api.logger.info(f'Writing settings for {module.text()}')

    def populate_settings_frame(self, parent_item, row=0):
        first_iteration = True
        for i in range(parent_item.rowCount()):
            child_item = parent_item.child(i)
            if isinstance(child_item.data(), str):
                row = self._ui_add_string_value_to_settings_frame(
                    child_item.text(),
                    child_item.data(),
                    row
                )
            elif isinstance(child_item.data(), bool):
                row = self._ui_add_bool_value_to_settings_frame(
                    child_item.text(),
                    child_item.data(),
                    row
                )
            elif isinstance(child_item.data(), list):
                row = self._ui_add_list_value_to_settings_frame(
                    child_item.text(),
                    child_item.data(),
                    row
                )
            elif isinstance(child_item.data(), int):
                row = self._ui_add_int_value_to_settings_frame(
                    child_item.text(),
                    child_item.data(),
                    row
                )
            elif isinstance(child_item.data(), float):
                row = self._ui_add_float_value_to_settings_frame(
                    child_item.text(),
                    child_item.data(),
                    row
                )
            elif child_item.data() is None:
                row = self._ui_add_group_label_to_settings_frame(
                    child_item.text(),
                    row=row,
                    first_iteration=first_iteration
                )
                row = self.populate_settings_frame(child_item, row=row)
            first_iteration=False
        return row + 1

    def clear_settings_frame(self):
        def _delete_children(layout):
            for i in reversed(range(layout.count())):
                item = layout.itemAt(i)
                if isinstance(item, (QtWidgets.QGridLayout, QtWidgets.QHBoxLayout, QtWidgets.QVBoxLayout)):
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
                file_path = os.path.join(
                    self.settings_file_dir,
                    module,
                    f'{module}_settings.json'
                )
                settings = self.get_settings_for_module(file_path)
            except FileNotFoundError as e:
                self.api.logger.warning(str(e))
                module_item.setData(e)
            else:
                self.add_settings_to_model_item(module_item, settings) # Must take in settings, as setting data will reorder

    def add_settings_to_model_item(self, parent_item, settings):
        """
        @param parent_item: QtStandardItem
        @param settings: dict()
        """
        for name, value in settings.items():
            child_item = QtGui.QStandardItem(name)
            parent_item.appendRow(child_item)
            if isinstance(value, dict):
                self.add_settings_to_model_item(child_item, value)
            else:
                child_item.setData(value)

    def on_str_value_changed(self):
        item = self.get_model_item_from_value_widget(self.sender())
        item.setData(self.sender().text())
        if self.api.debug:
            self.api.logger.debug(f'Setting {item.text()} to {item.data()}')

    def on_int_float_value_changed(self):
        item = self.get_model_item_from_value_widget(self.sender())
        item.setData(self.sender().value())
        if self.api.debug:
            self.api.logger.debug(f'Setting {item.text()} to {item.data()}')

    def on_bool_value_changed(self):
        item = self.get_model_item_from_value_widget(self.sender())
        item.setData(self.sender().isChecked())
        if self.api.debug:
            self.api.logger.debug(f'Setting {item.text()} to {item.data()}')

    def on_clicked_module(self):
        self.clear_settings_frame()

        module = self.get_selected_module_from_model()
        if module is None:
            return

        if self.api.debug:
            self.api.logger.debug(f'User clicked on {module.text()} inside settings dialog.')

        if isinstance(module.data(), FileNotFoundError):
            self.module_settings_layout.addWidget(QtWidgets.QLabel(str(module.data())))
        else:
            self.populate_settings_frame(module)

    def on_clicked_apply(self):
        for row in range(self.module_model.rowCount()):
            item = self.module_model.item(row, 0)

            file_path = os.path.join(
                self.settings_file_dir,
                item.text(),
                f'{item.text()}_settings.json'
            )

            self.write_module_settings(item, file_path)

    def on_clicked_ok(self):
        self.on_clicked_apply()
        self.close()

    def _create_ui(self):
        self._ui_frame_modules_list(0)
        self._ui_frame_module_settings(1)
        self._ui_frame_buttons(1)

    def _ui_frame_modules_list(self, col):
        self.main_layout.addWidget(bw_ui_tools.label('Loaded Modules'), 0, col)
        self._ui_add_module_view_widget(col)

    def _ui_frame_module_settings(self, col):
        self.main_layout.addWidget(bw_ui_tools.label('Module Settings'), 0, col)
        scroll_area = self._ui_add_scroll_area_widget(col)
        self._ui_add_settings_widget(scroll_area)

    def _ui_frame_buttons(self, col):
        layout = QtWidgets.QHBoxLayout()
        self.main_layout.addLayout(layout, 2, col)

        layout.addStretch()

        w = QtWidgets.QPushButton('Ok')
        layout.addWidget(w)
        w.clicked.connect(self.on_clicked_ok)

        w = QtWidgets.QPushButton('Cancel')
        w.clicked.connect(self.close)
        layout.addWidget(w)

        w = QtWidgets.QPushButton('Apply')
        w.clicked.connect(self.on_clicked_apply)
        layout.addWidget(w)

    def _ui_add_module_view_widget(self, col):
        self.module_view_widget.setFixedWidth(130)
        self.module_view_widget.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.main_layout.addWidget(self.module_view_widget, 1, col)
        self.module_view_widget.selectionModel().selectionChanged.connect(self.on_clicked_module)

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

    def _ui_add_group_label_to_settings_frame(self, name, row=0, first_iteration=False):
        # if not first_iteration:
        #     for _ in range(4):
        #         self.module_settings_layout.addWidget(bw_ui_tools.separator_frame(), row, 0, 1, 2)
        #         row += 1
        #     self.module_settings_layout.addWidget(bw_ui_tools.separator(), row, 0, 1, 2)
        #     row += 1
        self.module_settings_layout.addWidget(
            bw_ui_tools.label(name, alignment=QtCore.Qt.AlignLeft),
            row, 0, 1, 2
        )
        return row + 1

    def _ui_add_settings_to_settings_frame(self, settings, row=0):
        """
        Recursively popuplate the settings frame with appropiate widgets based on the value type
        @param settings: A dictionary read from a json file
        @param row: The row
        @return: The new row after all recursive calls
        """
        for key, value in settings.items():
            if isinstance(value, dict):
                for _ in range(4):
                    self.module_settings_layout.addWidget(bw_ui_tools.separator_frame(), row, 0, 1, 2)
                    row += 1
                self.module_settings_layout.addWidget(bw_ui_tools.separator(), row, 0, 1, 2)
                self.module_settings_layout.addWidget(
                    bw_ui_tools.label(key, alignment=QtCore.Qt.AlignLeft),
                    row + 1, 0, 1, 2
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
                self.module_settings_layout.addWidget(bw_ui_tools.label('Unsupported type.'))
            row += 1
        return row

    def _ui_add_string_value_to_settings_frame(self, name, value, row):
        self._ui_add_value_name_to_settings_frame(name, row)
        w = QtWidgets.QLineEdit()
        w.setText(value)
        w.textChanged.connect(self.on_str_value_changed)
        w.setStyleSheet(f'background : {self._value_background}')
        w.setAlignment(QtCore.Qt.AlignRight)
        self.module_settings_layout.addWidget(w, row, 1)
        return row + 1

    def _ui_add_list_value_to_settings_frame(self, name, value, row):
        self._ui_add_value_name_to_settings_frame(name, row)
        if not all(isinstance(elem, (str, bool, int, float)) for elem in value):
            self.module_settings_layout.addWidget(
                QtWidgets.QLabel('Only str, bool, int, float are supported values!'), row, 1
            )
            return row + 1

        string = ''
        for item in value:
            string += f'{str(item)};'
        w = QtWidgets.QLineEdit(string)
        w.textChanged.connect(self.on_str_value_changed)
        w.setStyleSheet(f'background : {self._value_background}')
        w.setAlignment(QtCore.Qt.AlignRight)
        self.module_settings_layout.addWidget(w, row, 1)
        return row + 1

    def _ui_add_float_value_to_settings_frame(self, name, value, row):
        self._ui_add_value_name_to_settings_frame(name, row)
        w = QtWidgets.QDoubleSpinBox()
        w.setMaximum(99999.0)
        w.setValue(value)
        w.setSingleStep(0.01)
        # w.valueChanged.connect(self.on_value_changed)
        w.setStyleSheet(
            'QDoubleSpinBox'
            '{'
            f'background : {self._value_background};'
            'color : #cccccc;'
            '}'
        )
        w.setAlignment(QtCore.Qt.AlignRight)
        self.module_settings_layout.addWidget(w, row, 1)
        return row + 1

    def _ui_add_int_value_to_settings_frame(self, name, value, row):
        self._ui_add_value_name_to_settings_frame(name, row)
        w = QtWidgets.QSpinBox()
        w.setMaximum(99999)
        w.setValue(value)
        w.valueChanged.connect(self.on_int_float_value_changed)
        w.setStyleSheet(
            'QSpinBox'
            '{'
            f'background : {self._value_background};'
            'color : #cccccc;'
            '}'
        )
        w.setAlignment(QtCore.Qt.AlignRight)
        self.module_settings_layout.addWidget(w, row, 1)
        return row + 1

    def _ui_add_bool_value_to_settings_frame(self, name, value, row):
        self._ui_add_value_name_to_settings_frame(name, row)
        w = QtWidgets.QCheckBox()
        w.setChecked(value)
        w.stateChanged.connect(self.on_bool_value_changed)
        w.setStyleSheet(
            'QCheckBox::indicator'
            '{'
            f'background-color: {self._value_background};'
            '}'
        )
        self.module_settings_layout.addWidget(w, row, 1, 1, 1, QtCore.Qt.AlignRight)
        return row + 1

    def _ui_add_value_name_to_settings_frame(self, name, row):
        w = QtWidgets.QLabel(name)
        self.module_settings_layout.addWidget(w, row, 0)
        return row + 1
