from functools import partial

import sd
from bw_tools.common import bw_api_tool


def print_node_info(api: bw_api_tool.BWAPITool):
    def _get_properties(category):
        ret = f"{category.name}:\n"
        for p in node.getProperties(category):
            value = node.getPropertyValueFromId(p.getId(), category)
            if value:
                value = value.get()
            ret += f"\t{p.getId()} : {value}\n"
        return ret

    for node in api.ui_mgr.getCurrentGraphSelection():
        ret = (
            f'{"=" * 20}\n'
            "Position:\n"
            f"\t{node.getPosition()}\n"
            "Definition:\n"
            f"\tIdentifier: {node.getIdentifier()}\n"
            f"\tID: {node.getDefinition().getId()}\n"
            f"\tLabel: {node.getDefinition().getLabel()}\n"
        )
        ret += _get_properties(sd.api.sdproperty.SDPropertyCategory.Annotation)
        ret += _get_properties(sd.api.sdproperty.SDPropertyCategory.Input)
        ret += _get_properties(sd.api.sdproperty.SDPropertyCategory.Output)
        ret += f'{"=" * 20}\n'
        print(ret)


def on_graph_created(graph_view_id, api: bw_api_tool.BWAPITool):
    toolbar = api.get_graph_view_toolbar(graph_view_id)
    if toolbar is None:
        toolbar = api.create_graph_view_toolbar(graph_view_id)

    action = toolbar.addAction("Info")
    action.setToolTip("Prints API information about the selected nodes.")
    action.triggered.connect(lambda: print_node_info(api))


def on_initialize(api: bw_api_tool.BWAPITool):
    api.register_on_graph_view_created_callback(
        partial(on_graph_created, api=api)
    )
