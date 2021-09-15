from PySide2 import QtWidgets, QtCore
from typing import Tuple, Optional
from bw_tools.common import bw_ui_tools

BACKGROUND = "#151515"
MIN_LABEL_WIDTH = 200


class SettingWidget(QtWidgets.QWidget):
    def __init__(self, label: str, parent=None):
        super().__init__(parent=parent)
        self.setLayout(QtWidgets.QHBoxLayout())
        self.layout().setContentsMargins(0, 0, 0, 0)
        self.setStyleSheet("border-radius: 0px; padding: 3px")

        label_widget = QtWidgets.QLabel(label)
        label_widget.setMinimumWidth(MIN_LABEL_WIDTH)
        self.layout().addWidget(label_widget)


class StringValueWidget(SettingWidget):
    def __init__(self, label: str, value: str, parent=None):
        super().__init__(label, parent=parent)

        line_edit = QtWidgets.QLineEdit(self)
        line_edit.setText(value)
        # line_edit.textChanged.connect(self.on_str_value_changed)
        line_edit.setStyleSheet(
            f"background : {BACKGROUND}; border-radius: 3px"
        )
        line_edit.setAlignment(QtCore.Qt.AlignRight)
        self.layout().addWidget(line_edit)


class BoolValueWidget(SettingWidget):
    def __init__(self, label: str, value: bool, parent=None):
        super().__init__(label, parent=parent)
        w = QtWidgets.QCheckBox()
        w.setChecked(value)
        # w.stateChanged.connect(self.on_bool_value_changed)
        self.layout().addWidget(w)
        self.layout().setAlignment(w, QtCore.Qt.AlignRight)


class FloatValueWidget(SettingWidget):
    def __init__(self, label: str, value: int, parent=None):
        super().__init__(label, parent=parent)

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
    def __init__(self, label: str, value: int, parent=None):
        super().__init__(label, parent=parent)

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
    def __init__(self, label: str, value: int, values: Tuple, parent=None):
        super().__init__(label, parent=parent)

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
    def __init__(
        self, label: str, value: Tuple[float, float, float, float], parent=None
    ):
        super().__init__(label, parent=parent)

        r = BWColorComponentSpinBox(color="red", parent=self)
        r.setValue(value[0])
        self.layout().addWidget(r)

        g = BWColorComponentSpinBox(color="green", parent=self)
        g.setValue(value[1])
        self.layout().addWidget(g)

        b = BWColorComponentSpinBox(color="blue", parent=self)
        b.setValue(value[2])
        self.layout().addWidget(b)

        a = BWColorComponentSpinBox(color="white", parent=self)
        a.setValue(value[3])

        self.layout().addWidget(a)


class BWGroupBox(QtWidgets.QGroupBox):
    def __init__(self, label: str, parent=None) -> None:
        super().__init__(parent=parent)
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
    def __init__(self, color=Optional[str], parent=None):
        super().__init__(parent=parent)
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
