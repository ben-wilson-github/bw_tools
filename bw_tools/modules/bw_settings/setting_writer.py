from PySide2 import QtGui

import json
from pathlib import Path

from typing import Dict, Any

from bw_tools.modules.bw_settings import settings_loader


def write_module_settings(module_item: QtGui.QStandardItem, file_path: Path):
    data = _build_dict(module_item, {})
    print(data)

    with open(file_path, "w") as settings_file:
        json.dump(data, settings_file, indent=4)


def _build_dict(parent_item: QtGui.QStandardItem, data: Dict[Any, Any]) -> Dict[Any, Any]:
    for row in range(parent_item.rowCount()):
        setting_item = parent_item.child(row)

        widget_property_item, value_property_item, list_property_item = settings_loader.get_setting_properties(setting_item)

        if value_property_item.data():  # Set to true when building the model when the setting has child settings
            result = _build_dict(value_property_item, {})
            data[setting_item.text()]["value"] = result
        
        if list_property_item is not None:
            data[setting_item.text()]["list"] = [list_property_item.child(i).data() for i in range(list_property_item.rowCount())]

        data[setting_item.text()] = {
            "widget": widget_property_item.child(0).data()
        }
        
        if value_property_item.rowCount() == 1:

            item = value_property_item.child(0)
            if list_property_item:
                values = list_property_item.index(item.text())
            else:
                data_type = type(item.data())
                values = data_type(item.text())
        else:
            values = [type(value_property_item.child(i).data())(value_property_item.child(i).text()) for i in range(value_property_item.rowCount())]
        data[setting_item.text()]["value"] = values

        FIGURE OUT HOW TO WRITE THE DICT
    return data


    #     widget_property_item, value_property_item, list_property_item = settings_loader.get_setting_properties(setting_item)
        
    #     CONTINUE BUILDING DICT
    #     possible_values = settings_loader.get_possible_values(list_property_item)
    #     widget_type = settings_loader.WidgetTypes(widget_property_item.child(0).data())

    #     widget_type = self.get_widget_type(setting_item)
    #     value_item = self.get_child_item_with_key(
    #         setting_item, "value"
    #     )
    #     value = value_item.data()

    #     data[setting_name] = {}

    #     if widget_type is WidgetTypes.GROUPBOX:
    #         value = _build_dict(value_item, {})
    #     elif widget_type is WidgetTypes.COMBOBOX:
    #         data[setting_name]["list"] = self.get_combobox_list(
    #             setting_item
    #         )
    #     else:
    #         value = value_item.data()

    #     data[setting_name]["widget"] = widget_type.value
    #     data[setting_name]["value"] = value
    # return data