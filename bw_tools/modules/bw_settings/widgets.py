from typing import Any, Optional, Tuple

from bw_tools.modules.bw_settings.bw_settings_model import BWModuleModel
from PySide2.QtCore import Qt
from PySide2.QtGui import QStandardItem
from PySide2.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDataWidgetMapper,
    QDoubleSpinBox,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

BACKGROUND = "#151515"
MIN_LABEL_WIDTH = 200


class BWSettingWidget(QWidget):
    def __init__(self, label: str, value_item: QStandardItem = None):
        super().__init__(parent=None)
        self.value_item = value_item

        self.setLayout(QHBoxLayout())
        self.layout().setContentsMargins(0, 0, 0, 0)
        self.setStyleSheet("border-radius: 0px; padding: 3px")

        label_widget = QLabel(label)
        label_widget.setMinimumWidth(MIN_LABEL_WIDTH)
        self.layout().addWidget(label_widget)

    def set_up_mapper(
        self,
        model: BWModuleModel,
        widget: QWidget,
        column: int,
        parent_item: QStandardItem,
    ):
        self.mapper = QDataWidgetMapper()
        self.mapper.setModel(model)
        self.mapper.addMapping(widget, column)
        self.mapper.setRootIndex(model.indexFromItem(parent_item))
        self.mapper.toFirst()


class BWStringValueWidget(BWSettingWidget):
    def __init__(
        self,
        label: str,
        possible_values: Tuple[Any],
        value_property_item: QStandardItem,
        model: BWModuleModel,
    ):
        super().__init__(label)

        line_edit = QLineEdit(self)
        # line_edit.setText(values[0])
        # line_edit.textChanged.connect(self.on_str_value_changed)
        line_edit.setStyleSheet(f"background : {BACKGROUND}; border-radius: 3px")
        line_edit.setAlignment(Qt.AlignRight)
        self.layout().addWidget(line_edit)

        self.set_up_mapper(model, line_edit, 0, value_property_item)
        line_edit.textChanged.connect(self.mapper.submit)


class BWBoolValueWidget(BWSettingWidget):
    def __init__(
        self,
        label: str,
        possible_values: Tuple[bool],
        value_property_item: QStandardItem,
        model: BWModuleModel,
    ):
        super().__init__(label)
        w = QCheckBox()
        self.layout().addWidget(w)
        self.layout().setAlignment(w, Qt.AlignRight)

        self.set_up_mapper(model, w, 0, value_property_item)
        w.stateChanged.connect(self.mapper.submit)


class BWFloatValueWidget(BWSettingWidget):
    def __init__(
        self,
        label: str,
        possible_values: Tuple[bool],
        value_property_item: QStandardItem,
        model: BWModuleModel,
    ):
        super().__init__(label)

        w = QDoubleSpinBox(self)
        w.setMaximum(999)
        # w.valueChanged.connect(self.on_int_float_value_changed)
        w.setStyleSheet("QDoubleSpinBox" "{" f"background : {BACKGROUND};" "color : #cccccc;" "border-radius: 3px;" "}")
        w.setMaximumWidth(50)
        w.setAlignment(Qt.AlignRight)
        self.layout().addWidget(w)

        self.set_up_mapper(model, w, 0, value_property_item)
        w.valueChanged.connect(self.mapper.submit)


class BWIntValueWidget(BWSettingWidget):
    def __init__(
        self,
        label: str,
        possible_values: Tuple[bool],
        value_property_item: QStandardItem,
        model: BWModuleModel,
    ):
        super().__init__(label, value_property_item)

        self.widget = QSpinBox(self)
        self.widget.setMaximum(999)
        self.widget.setStyleSheet(
            "QSpinBox" "{" f"background : {BACKGROUND};" "color : #cccccc;" "border-radius: 3px;" "}"
        )
        self.widget.setMaximumWidth(50)
        self.widget.setAlignment(Qt.AlignRight)
        self.layout().addWidget(self.widget)

        self.set_up_mapper(model, self.widget, 0, value_property_item)
        self.widget.valueChanged.connect(self.mapper.submit)


class BWDropDownWidget(BWSettingWidget):
    def __init__(
        self,
        label: str,
        possible_values: Tuple[bool],
        value_property_item: QStandardItem,
        model: BWModuleModel,
    ):
        super().__init__(label)

        combo = QComboBox()
        combo.addItems(possible_values)
        combo.setStyleSheet("QComboBox" "{" f"background: {BACKGROUND};" "color: #cccccc;" "border-radius: 3px;" "}")
        # combo.currentIndexChanged.connect(self.on_combobox_value_changed)
        self.layout().addWidget(combo)

        self.set_up_mapper(model, combo, 0, value_property_item)


class BWRGBAValueWidget(BWSettingWidget):
    def __init__(
        self,
        label: str,
        possible_values: Tuple[bool],
        value_property_item: QStandardItem,
        model: BWModuleModel,
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
        self.r.valueChanged.connect(self.mapper_r.submit)
        self.g.valueChanged.connect(self.mapper_g.submit)
        self.b.valueChanged.connect(self.mapper_b.submit)
        self.a.valueChanged.connect(self.mapper_a.submit)

    def set_up_mapper(self, model: BWModuleModel, parent_item: QStandardItem):
        self.mapper_r = QDataWidgetMapper()
        self.mapper_r.setModel(model)
        self.mapper_r.addMapping(self.r, 0)
        self.mapper_r.setRootIndex(model.indexFromItem(parent_item))
        self.mapper_r.setCurrentIndex(0)

        self.mapper_g = QDataWidgetMapper()
        self.mapper_g.setModel(model)
        self.mapper_g.addMapping(self.g, 0)
        self.mapper_g.setRootIndex(model.indexFromItem(parent_item))
        self.mapper_g.setCurrentIndex(1)

        self.mapper_b = QDataWidgetMapper()
        self.mapper_b.setModel(model)
        self.mapper_b.addMapping(self.b, 0)
        self.mapper_b.setRootIndex(model.indexFromItem(parent_item))
        self.mapper_b.setCurrentIndex(2)

        self.mapper_a = QDataWidgetMapper()
        self.mapper_a.setModel(model)
        self.mapper_a.addMapping(self.a, 0)
        self.mapper_a.setRootIndex(model.indexFromItem(parent_item))
        self.mapper_a.setCurrentIndex(3)


class BWGroupBox(QGroupBox):
    def __init__(self, label: str) -> None:
        super().__init__(parent=None)
        self.setTitle(label)
        self.setFlat(False)

        self.setLayout(QVBoxLayout())
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


class BWColorComponentSpinBox(QDoubleSpinBox):
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
        self.setAlignment(Qt.AlignCenter)
