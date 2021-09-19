from PySide2 import QtGui

import json
from pathlib import Path

from typing import Dict, Any

from bw_tools.modules.bw_settings import settings_loader


def write_module_settings(module_item: QtGui.QStandardItem, file_path: Path):
    data = _build_dict(module_item, {})

    with open(file_path, "w") as settings_file:
        json.dump(data, settings_file, indent=4)


def _build_dict(
    parent_item: QtGui.QStandardItem, data: Dict[Any, Any]
) -> Dict[Any, Any]:
    for row in range(parent_item.rowCount()):
        setting_item = parent_item.child(row)
        setting_name = setting_item.text()
        data[setting_name] = dict()

        (
            widget_property_item,
            value_property_item,
            list_property_item,
            content_property_item,
        ) = settings_loader.get_setting_property_items(setting_item)

        if widget_property_item is not None:
            data[setting_name]["widget"] = widget_property_item.child(0).data()

        if list_property_item is not None:
            data[setting_name]["list"] = [
                list_property_item.child(i).data()
                for i in range(list_property_item.rowCount())
            ]

        if value_property_item is not None:
            value = _get_value_from_item(value_property_item)
            data[setting_item.text()]["value"] = value

        if content_property_item is not None:
            result = _build_dict(content_property_item, {})
            data[setting_item.text()]["content"] = result

    return data


def _get_value_from_item(value_property_item: QtGui.QStandardItem) -> Any:
    # Value propertie are updated in the QStandardItem.text()
    # function, due to them being controlled by QDataWidgetMappers.
    # Therefore, must cast str to appropriate data type
    if value_property_item.rowCount() == 1:
        value_item = value_property_item.child(0)

        # If a bool, must manually cast to bool
        if isinstance(value_item.data(), bool):
            value = value_item.text().lower() == "true"
        else:  # otherwise regular cast will work
            data_type = type(value_item.data())
            value = data_type(value_item.text())
    else:
        value = [
            type(value_property_item.child(i).data())(
                value_property_item.child(i).text()
            )
            for i in range(value_property_item.rowCount())
        ]
    return value
