from PySide2 import QtWidgets, QtCore, QtGui
from typing import Tuple, Optional
from bw_tools.common import bw_ui_tools
from bw_tools.modules.bw_settings.bw_settings_model import ModuleModel

BACKGROUND = "#151515"
MIN_LABEL_WIDTH = 200


class SettingWidget(QtWidgets.QWidget):
    def __init__(self, label: str):
        super().__init__(parent=None)
        self.setLayout(QtWidgets.QHBoxLayout())
        self.layout().setContentsMargins(0, 0, 0, 0)
        self.setStyleSheet("border-radius: 0px; padding: 3px")

        label_widget = QtWidgets.QLabel(label)
        label_widget.setMinimumWidth(MIN_LABEL_WIDTH)
        self.layout().addWidget(label_widget)


class StringValueWidget(SettingWidget):
    def __init__(
        self,
        label: str,
        value: str,
        model: ModuleModel,
        item: QtGui.QStandardItem,
    ):
        super().__init__(label)

        line_edit = QtWidgets.QLineEdit(self)
        line_edit.setText(value)
        # line_edit.textChanged.connect(self.on_str_value_changed)
        line_edit.setStyleSheet(
            f"background : {BACKGROUND}; border-radius: 3px"
        )
        line_edit.setAlignment(QtCore.Qt.AlignRight)
        self.layout().addWidget(line_edit)

        self.mapper = QtWidgets.QDataWidgetMapper()
        self.mapper.setModel(model)
        self.mapper.addMapping(line_edit, 0)
        print(item.text())
        self.mapper.setRootIndex(model.indexFromItem(item))


class BoolValueWidget(SettingWidget):
    def __init__(self, label: str, value: bool):
        super().__init__(label)
        w = QtWidgets.QCheckBox()
        w.setChecked(value)
        # w.stateChanged.connect(self.on_bool_value_changed)
        self.layout().addWidget(w)
        self.layout().setAlignment(w, QtCore.Qt.AlignRight)


class FloatValueWidget(SettingWidget):
    def __init__(self, label: str, value: int):
        super().__init__(label)

        w = QtWidgets.QDoubleSpinBox(self)
        w.setMaximum(999)
        w.setValue(value)
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


class IntValueWidget(SettingWidget):
    def __init__(self, label: str, value: int):
        super().__init__(label)

        w = QtWidgets.QSpinBox(self)
        w.setMaximum(999)
        w.setValue(value)
        # w.valueChanged.connect(self.on_int_float_value_changed)
        w.setStyleSheet(
            "QSpinBox"
            "{"
            f"background : {BACKGROUND};"
            "color : #cccccc;"
            "border-radius: 3px;"
            "}"
        )
        w.setMaximumWidth(50)
        w.setAlignment(QtCore.Qt.AlignRight)
        self.layout().addWidget(w)


class DropDownWidget(SettingWidget):
    def __init__(self, label: str, value: int, values: Tuple):
        super().__init__(label)

        combo = QtWidgets.QComboBox()
        combo.addItems(values)
        combo.setCurrentIndex(value)
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


class RGBAValueWidget(SettingWidget):
    def __init__(self, label: str, value: Tuple[float, float, float, float]):
        super().__init__(label)

        r = BWColorComponentSpinBox(color="red")
        r.setValue(value[0])
        self.layout().addWidget(r)

        g = BWColorComponentSpinBox(color="green")
        g.setValue(value[1])
        self.layout().addWidget(g)

        b = BWColorComponentSpinBox(color="blue")
        b.setValue(value[2])
        self.layout().addWidget(b)

        a = BWColorComponentSpinBox(color="white")
        a.setValue(value[3])

        self.layout().addWidget(a)


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
