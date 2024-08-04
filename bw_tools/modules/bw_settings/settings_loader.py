from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING, Any, List, Tuple, Type

from bw_tools.modules.bw_settings.bw_settings_model import BWModuleModel
from bw_tools.modules.bw_settings.widgets import (
    BWBoolValueWidget,
    BWDropDownWidget,
    BWFloatValueWidget,
    BWGroupBox,
    BWIntValueWidget,
    BWRGBAValueWidget,
    BWSettingWidget,
    BWStringValueWidget,
)
from PySide6.QtWidgets import QLabel, QLayout, QVBoxLayout, QWidget

if TYPE_CHECKING:
    from PySide6.QtGui import QStandardItem, QStandardItemModel


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
    WidgetTypes.LINEEDIT.value: BWStringValueWidget,
    WidgetTypes.SPINBOXFLOAT.value: BWFloatValueWidget,
    WidgetTypes.SPINBOXINT.value: BWIntValueWidget,
    WidgetTypes.CHECKBOX.value: BWBoolValueWidget,
    WidgetTypes.COMBOBOX.value: BWDropDownWidget,
    WidgetTypes.RGBA.value: BWRGBAValueWidget,
}


def get_setting_property_items(
    setting_item: QStandardItem,
) -> Tuple[QStandardItem, QStandardItem, QStandardItem, QStandardItem]:
    widget_item = None
    value_item = None
    list_item = None
    content_item = None
    for i in range(setting_item.rowCount()):
        text = setting_item.child(i).text()
        if text == "widget":
            widget_item = setting_item.child(i)
        elif text == "value":
            value_item = setting_item.child(i)
        elif text == "list":
            list_item = setting_item.child(i)
        elif text == "content":
            content_item = setting_item.child(i)
    return widget_item, value_item, list_item, content_item


def get_module_widget(module_item: QStandardItem, model: QStandardItemModel) -> QWidget:
    if isinstance(module_item.data(), FileNotFoundError):
        return QLabel(str(module_item.data()))

    module_widget = QWidget()
    module_widget.setLayout(QVBoxLayout())
    module_widget.layout().setContentsMargins(0, 0, 0, 0)

    for i in range(module_item.rowCount()):
        setting_item = module_item.child(i)
        _add_setting_to_layout(module_widget.layout(), setting_item, model)

    return module_widget


def _add_setting_to_layout(
    layout: QLayout,
    setting_item: QStandardItem,
    model: BWModuleModel,
):
    """
    Dynamically adds settings to a given layout based on model.

    For each setting, an appropiate widget is selected based on
    the widget type map. Each widget is connected to the model
    via a QDataWidgetMapper. The widget is responsible for
    correctly setting this up.
    """
    (
        widget_property_item,
        value_property_item,
        list_property_item,
        content_property_item,
    ) = get_setting_property_items(setting_item)

    setting_name = setting_item.text()
    widget_type = WidgetTypes(widget_property_item.child(0).data())

    if widget_type is WidgetTypes.GROUPBOX:
        _add_group_box_to_layout(
            setting_name,
            WIDGET_MAP[widget_type.value],
            content_property_item,
            layout,
            model,
        )
        return

    possible_values = []
    if list_property_item is not None:
        possible_values = _get_possible_values(list_property_item)

    _add_widget_to_layout(
        setting_name,
        WIDGET_MAP[widget_type.value],
        possible_values,
        value_property_item,
        layout,
        model,
    )


def _add_widget_to_layout(
    setting_name: str,
    widget_constructor: Type[BWSettingWidget],
    possible_values: List,
    value_property_item: QStandardItem,
    layout: QLayout,
    model: QStandardItemModel,
):
    w = widget_constructor(setting_name, possible_values, value_property_item, model)
    layout.addWidget(w)


def _add_group_box_to_layout(
    setting_name: str,
    widget_constructor: Type[BWSettingWidget],
    content_property_item: QStandardItem,
    layout: QLayout,
    model: QStandardItemModel,
):
    w = widget_constructor(setting_name)
    layout.addWidget(w)

    for i in range(content_property_item.rowCount()):
        _add_setting_to_layout(w.layout(), content_property_item.child(i), model)
    return


def _get_possible_values(list_property_item: QStandardItem) -> List[Any]:
    return [list_property_item.child(i).text() for i in range(list_property_item.rowCount())]
