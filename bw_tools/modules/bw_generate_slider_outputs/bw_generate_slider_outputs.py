import sd
from sd.api.sdhistoryutils import SDHistoryUtils
from common import bw_api_tool
import math


def sort_nodes_by_y(node_list):
    sorted_list = list(node_list)
    swapped = True
    while swapped:
        swapped = False
        for i in range(len(sorted_list) - 1):
            if sorted_list[i].getPosition().y > sorted_list[i + 1].getPosition().y:
                sorted_list[i], sorted_list[i + 1] = sorted_list[i + 1], sorted_list[i]
                swapped = True
    return tuple(sorted_list)


def set_float_value(node, id, value):
    node.setInputPropertyValueFromId(
        id,
        sd.api.sdvaluefloat.SDValueFloat.sNew(value)
    )


def set_string_value(node, id, value):
    node.setInputPropertyValueFromId(
        id,
        sd.api.sdvaluestring.SDValueString.sNew(value)
    )


def set_float_2_value(node, id, v1, v2):
    node.setInputPropertyValueFromId(
        id,
        sd.api.sdvaluefloat2.SDValueFloat2.sNew(sd.api.sdbasetypes.float2(v1, v2))
    )


def set_int_value(node, id, value):
    node.setInputPropertyValueFromId(
        id,
        sd.api.sdvalueint.SDValueInt.sNew(value)
    )


def generate_slider_outputs(api: bw_api_tool.APITool):
    increment = 0.02

    nodes = sort_nodes_by_y(api.current_selection)
    with SDHistoryUtils.UndoGroup('Straighten Connection Undo Group'):
        for i, node in enumerate(nodes):
            # set_float_value(node, 'accurate_cell_size_transition', i * increment)
            # set_float_2_value(node, 'text', -1 * (i * increment), i * increment)
            set_string_value(node, 'text', f'Accurate Cell Size Transition: {round(i * increment, 2)}')
            # set_int_value(node, 'alignment', 0)
    return


def on_initialize(api: bw_api_tool.APITool):
    action = api.toolbar.addAction('Slider Output')
    action.triggered.connect(lambda: generate_slider_outputs(api))
