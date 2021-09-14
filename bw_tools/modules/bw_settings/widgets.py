from PySide2 import QtWidgets, QtCore
from typing import Union, Tuple, Optional

BACKGROUND = "#151515"
MIN_LABEL_WIDTH = 200


class SettingWidget(QtWidgets.QWidget):
    def __init__(self, label: str, parent=None):
        super().__init__(parent=parent)
        self.setLayout(QtWidgets.QGridLayout())
        self.layout().setContentsMargins(0, 0, 0, 0)
        self.setStyleSheet("border-radius: 0px; padding: 3px")

        label_widget = QtWidgets.QLabel(label)
        label_widget.setMinimumWidth(MIN_LABEL_WIDTH)
        self.layout().addWidget(label_widget, 0, 0)


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
        self.layout().addWidget(line_edit, 0, 1)


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
        self.layout().addWidget(w, 0, 1)


class RGBAValueWidget(SettingWidget):
    def __init__(
        self, label: str, value: Tuple[float, float, float, float], parent=None
    ):
        super().__init__(label, parent=parent)

        r = SettingDoubleSpinBox(color="red", parent=self)
        r.setValue(value[0])
        self.layout().addWidget(r, 0, 1)

        g = SettingDoubleSpinBox(color="green", parent=self)
        g.setValue(value[1])
        self.layout().addWidget(g, 0, 2)

        b = SettingDoubleSpinBox(color="blue", parent=self)
        b.setValue(value[2])
        self.layout().addWidget(b, 0, 3)

        a = SettingDoubleSpinBox(color="white", parent=self)
        a.setValue(value[3])

        self.layout().addWidget(a, 0, 4)


class SettingDoubleSpinBox(QtWidgets.QDoubleSpinBox):
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
