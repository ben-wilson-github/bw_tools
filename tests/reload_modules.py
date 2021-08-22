import importlib

from bw_tools.common import (
    bw_chain_dimension,
    bw_node,
    bw_node_selection,
    bw_api_tool,
)
from bw_tools.modules.bw_layout_graph import (
    aligner_mainline,
    aligner_vertical,
    alignment_behavior,
    bw_layout_graph,
    layout_node,
    node_sorting,
)
from bw_tools.modules.bw_settings import (
    bw_settings,
    bw_settings_dialog,
    bw_settings_model,
)


modules = [
    bw_settings,
    bw_settings_dialog,
    bw_settings_model,
    bw_node,
    node_sorting,
    aligner_vertical,
    bw_layout_graph,
    bw_node_selection,
    bw_chain_dimension,
    alignment_behavior,
    layout_node,
    aligner_mainline,
    bw_api_tool,
]


def reload_modules():
    for module in modules:
        print(f"Reloading {str(module)}")
        importlib.reload(module)
