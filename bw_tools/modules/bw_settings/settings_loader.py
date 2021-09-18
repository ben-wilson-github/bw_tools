from __future__ import annotations
from enum import Enum
from typing import TYPE_CHECKING, Any, Tuple

from bw_tools.modules.bw_settings.widgets import (
    BoolValueWidget,
    BWGroupBox,
    DropDownWidget,
    FloatValueWidget,
    IntValueWidget,
    RGBAValueWidget,
    StringValueWidget,
)


from PySide2.QtWidgets import (
    QLayout,
    QGridLayout,
    QHBoxLayout,
    QVBoxLayout,
    QWidget,
    QLabel,
)

if TYPE_CHECKING:
    from PySide2.QtGui import QStandardItem, QStandardItemModel


class WidgetTypes(Enum):
    GROUPBOX = 0
    LINEEDIT = 1
    SPINBOXINT = 2
    SPINBOXFLOAT = 3
    CHECKBOX = 4
    COMBOBOX = 5
    RGBA = 6


WIDGET_MAP = {
    WidgetTypes.GROUPBOX.value: BWGroupBox,
    WidgetTypes.LINEEDIT.value: StringValueWidget,
    WidgetTypes.SPINBOXFLOAT.value: FloatValueWidget,
    WidgetTypes.SPINBOXINT.value: IntValueWidget,
    WidgetTypes.CHECKBOX.value: BoolValueWidget,
    WidgetTypes.COMBOBOX.value: DropDownWidget,
    WidgetTypes.RGBA.value: RGBAValueWidget,
}


def clear_layout(layout: QLayout):
    def _delete_children(layout):
        for i in reversed(range(layout.count())):
            item = layout.itemAt(i)
            if isinstance(
                item,
                (
                    QGridLayout,
                    QHBoxLayout,
                    QVBoxLayout,
                ),
            ):
                _delete_children(item)
            else:
                widget = item.widget()
                widget.deleteLater()

    _delete_children(layout)


def get_module_widget(
    module_item: QStandardItem, model: QStandardItemModel
) -> QWidget:
    if isinstance(module_item.data(), FileNotFoundError):
        return QLabel(str(module_item.data()))

    module_widget = QWidget()
    module_widget.setLayout(QVBoxLayout())
    module_widget.layout().setContentsMargins(0, 0, 0, 0)

    for i in range(module_item.rowCount()):
        setting_item = module_item.child(i)
        add_setting_to_layout(module_widget.layout(), setting_item, model)

    return module_widget


def add_setting_to_layout(
    layout: QLayout,
    setting_item: QStandardItem,
    model: QStandardItemModel,
):
    (
        widget_property_item,
        value_property_item,
        list_property_item,
    ) = _get_setting_properties_from_model(setting_item)

    setting_name = setting_item.text()
    possible_values = _get_possible_values(list_property_item)
    value_items_in_model = _get_value_items(value_property_item)
    values = _get_values(value_items_in_model)
    widget_type = WidgetTypes(widget_property_item.child(0).data())

    if widget_type is WidgetTypes.GROUPBOX:
        widget_constructor = WIDGET_MAP[widget_type.value]
        w = widget_constructor(setting_name)
        layout.addWidget(w)

        for i in range(value_property_item.rowCount()):
            add_setting_to_layout(
                w.layout(), value_property_item.child(i), model
            )
        return

    widget_constructor = WIDGET_MAP[widget_type.value]
    w = widget_constructor(
        setting_name, values, possible_values, value_items_in_model, model
    )
    layout.addWidget(w)


def _get_possible_values(list_property_item: QStandardItem) -> Tuple[Any, ...]:
    if list_property_item is None:
        return None
    return [
        list_property_item.child(i).data()
        for i in range(list_property_item.rowCount())
    ]


def _get_setting_properties_from_model(
    setting_item: QStandardItem,
) -> Tuple[QStandardItem, QStandardItem, QStandardItem]:
    widget_item = None
    value_item = None
    list_item = None
    for i in range(setting_item.rowCount()):
        text = setting_item.child(i).text()
        if text == "widget":
            widget_item = setting_item.child(i)
        elif text == "value":
            value_item = setting_item.child(i)
        elif text == "list":
            list_item = setting_item.child(i)
    return widget_item, value_item, list_item


def _get_value_items(
    value_item: QStandardItem,
) -> Tuple[QStandardItem, ...]:
    if value_item.rowCount() > 1:
        return [value_item.child(i) for i in range(value_item.rowCount())]
    else:
        return [value_item.child(0)]


def _get_values(value_items: Tuple[QStandardItem]) -> Tuple(Any, ...):
    return [value.data() for value in value_items]
