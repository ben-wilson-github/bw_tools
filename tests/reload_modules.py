import importlib

from bw_tools.common import bw_chain_dimension, bw_node, bw_node_selection
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

importlib.reload(bw_settings)
importlib.reload(bw_settings_dialog)
importlib.reload(bw_settings_model)
importlib.reload(bw_node)
importlib.reload(node_sorting)
importlib.reload(aligner_vertical)
importlib.reload(bw_layout_graph)
importlib.reload(bw_node_selection)
importlib.reload(bw_chain_dimension)
importlib.reload(alignment_behavior)
importlib.reload(layout_node)
importlib.reload(aligner_mainline)
