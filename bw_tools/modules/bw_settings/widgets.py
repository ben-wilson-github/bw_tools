from abc import ABC, abstractmethod
from PySide2 import QtWidgets, QtCore, QtGui
from typing import Tuple, Optional, List, Any
from bw_tools.common import bw_ui_tools
from bw_tools.modules.bw_settings.bw_settings_model import ModuleModel
from dataclasses import dataclass

BACKGROUND = "#151515"
MIN_LABEL_WIDTH = 200


class SettingWidget(QtWidgets.QWidget):
    def __init__(self, label: str, value_item: QtGui.QStandardItem = None):
        super().__init__(parent=None)
        self.value_item = value_item

        self.setLayout(QtWidgets.QHBoxLayout())
        self.layout().setContentsMargins(0, 0, 0, 0)
        self.setStyleSheet("border-radius: 0px; padding: 3px")

        label_widget = QtWidgets.QLabel(label)
        label_widget.setMinimumWidth(MIN_LABEL_WIDTH)
        self.layout().addWidget(label_widget)

    def set_up_mapper(
        self,
        model: ModuleModel,
        widget: QtWidgets.QWidget,
        column: int,
        parent_item: QtGui.QStandardItem,
    ):
        self.mapper = QtWidgets.QDataWidgetMapper()
        self.mapper.setModel(model)
        self.mapper.addMapping(widget, column)
        self.mapper.setRootIndex(model.indexFromItem(parent_item))
        self.mapper.toFirst()


class StringValueWidget(SettingWidget):
    def __init__(
        self,
        label: str,
        possible_values: Tuple[Any],
        value_property_item: QtGui.QStandardItem,
        model: ModuleModel,
    ):
        super().__init__(label)

        line_edit = QtWidgets.QLineEdit(self)
        # line_edit.setText(values[0])
        # line_edit.textChanged.connect(self.on_str_value_changed)
        line_edit.setStyleSheet(
            f"background : {BACKGROUND}; border-radius: 3px"
        )
        line_edit.setAlignment(QtCore.Qt.AlignRight)
        self.layout().addWidget(line_edit)

        self.set_up_mapper(model, line_edit, 0, value_property_item)


class BoolValueWidget(SettingWidget):
    def __init__(
        self,
        label: str,
        possible_values: Tuple[bool],
        value_property_item: QtGui.QStandardItem,
        model: ModuleModel,
    ):
        super().__init__(label)
        w = QtWidgets.QCheckBox()
        self.layout().addWidget(w)
        self.layout().setAlignment(w, QtCore.Qt.AlignRight)

        self.set_up_mapper(model, w, 0, value_property_item)


class FloatValueWidget(SettingWidget):
    def __init__(
        self,
        label: str,
        possible_values: Tuple[bool],
        value_property_item: QtGui.QStandardItem,
        model: ModuleModel,
    ):
        super().__init__(label)

        w = QtWidgets.QDoubleSpinBox(self)
        w.setMaximum(999)
        # w.valueChanged.connect(self.on_int_float_value_changed)
        w.setStyleSheet(
            "QDoubleSpinBox"
            "{"
            f"background : {BACKGROUND};"
            "color : #cccccc;"
            "border-radius: 3px;"
            "}"
        )
        w.setMaximumWidth(50)
        w.setAlignment(QtCore.Qt.AlignRight)
        self.layout().addWidget(w)

        self.set_up_mapper(model, w, 0, value_property_item)


class IntValueWidget(SettingWidget):
    def __init__(
        self,
        label: str,
        possible_values: Tuple[bool],
        value_property_item: QtGui.QStandardItem,
        model: ModuleModel,
    ):
        super().__init__(label, value_property_item)

        self.widget = QtWidgets.QSpinBox(self)
        self.widget.setMaximum(999)
        self.widget.setStyleSheet(
            "QSpinBox"
            "{"
            f"background : {BACKGROUND};"
            "color : #cccccc;"
            "border-radius: 3px;"
            "}"
        )
        self.widget.setMaximumWidth(50)
        self.widget.setAlignment(QtCore.Qt.AlignRight)
        self.layout().addWidget(self.widget)

        self.set_up_mapper(model, self.widget, 0, value_property_item)


class DropDownWidget(SettingWidget):
    def __init__(
        self,
        label: str,
        possible_values: Tuple[bool],
        value_property_item: QtGui.QStandardItem,
        model: ModuleModel,
    ):
        super().__init__(label)

        combo = QtWidgets.QComboBox()
        combo.addItems(possible_values)
        combo.setStyleSheet(
            "QComboBox"
            "{"
            f"background: {BACKGROUND};"
            "color: #cccccc;"
            "border-radius: 3px;"
            "}"
        )
        # combo.currentIndexChanged.connect(self.on_combobox_value_changed)
        self.layout().addWidget(combo)

        self.set_up_mapper(model, combo, 0, value_property_item)


class RGBAValueWidget(SettingWidget):
    def __init__(
        self,
        label: str,
        possible_values: Tuple[bool],
        value_property_item: QtGui.QStandardItem,
        model: ModuleModel,
    ):
        super().__init__(label)

        self.r = BWColorComponentSpinBox(color="red")
        self.layout().addWidget(self.r)

        self.g = BWColorComponentSpinBox(color="green")
        self.layout().addWidget(self.g)

        self.b = BWColorComponentSpinBox(color="blue")
        self.layout().addWidget(self.b)

        self.a = BWColorComponentSpinBox(color="white")
        self.layout().addWidget(self.a)

        self.set_up_mapper(model, value_property_item)

    def set_up_mapper(
        self, model: ModuleModel, parent_item: QtGui.QStandardItem
    ):
        self.mapper_r = QtWidgets.QDataWidgetMapper()
        self.mapper_r.setModel(model)
        self.mapper_r.addMapping(self.r, 0)
        self.mapper_r.setRootIndex(model.indexFromItem(parent_item))
        self.mapper_r.setCurrentIndex(0)

        self.mapper_g = QtWidgets.QDataWidgetMapper()
        self.mapper_g.setModel(model)
        self.mapper_g.addMapping(self.g, 0)
        self.mapper_g.setRootIndex(model.indexFromItem(parent_item))
        self.mapper_g.setCurrentIndex(1)

        self.mapper_b = QtWidgets.QDataWidgetMapper()
        self.mapper_b.setModel(model)
        self.mapper_b.addMapping(self.b, 0)
        self.mapper_b.setRootIndex(model.indexFromItem(parent_item))
        self.mapper_b.setCurrentIndex(2)

        self.mapper_a = QtWidgets.QDataWidgetMapper()
        self.mapper_a.setModel(model)
        self.mapper_a.addMapping(self.a, 0)
        self.mapper_a.setRootIndex(model.indexFromItem(parent_item))
        self.mapper_a.setCurrentIndex(3)


class BWGroupBox(QtWidgets.QGroupBox):
    def __init__(self, label: str) -> None:
        super().__init__(parent=None)
        self.setTitle(label)
        self.setFlat(False)

        self.setLayout(QtWidgets.QVBoxLayout())
        self.layout().setContentsMargins(0, 0, 0, 0)
        self.setStyleSheet(
            "QGroupBox {"
            "border-radius: 0px;"
            # "border-bottom: 1px solid #333333;"
            "padding-left: 15px;"
            "padding-right: 0px;"
            "padding-top: 10px;"
            "padding-bottom: 5px;"
            "}"
            "QGroupBox::title {"
            "background-color: transparent;"
            "padding-left: 0px;"
            "color: gray;"
            "}"
        )


class BWColorComponentSpinBox(QtWidgets.QDoubleSpinBox):
    def __init__(self, color=Optional[str]):
        super().__init__(parent=None)
        self.setMinimumWidth(50)
        self.setMaximum(1.0)
        self.setMinimum(0.0)
        self.setSingleStep(0.01)
        self.setStyleSheet(
            "QDoubleSpinBox"
            "{"
            f"background : {BACKGROUND};"
            "color : #cccccc;"
            "border-radius: 3px;"
            f"border-left: 1px solid {color};"
            "}"
        )
        self.setAlignment(QtCore.Qt.AlignCenter)
