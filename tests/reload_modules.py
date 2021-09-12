import importlib

from bw_tools.common import (
    bw_api_tool,
    bw_chain_dimension,
    bw_node,
    bw_node_selection,
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
from bw_tools.modules.bw_straighten_connection import (
    bw_straighten_connection,
    straighten_behavior,
    straighten_node,
)
from bw_tools.modules.bw_optimize_graph import (
    bw_optimize_graph,
    optimizer,
    uniform_color_optimizer,
    comp_graph_optimizer,
    atomic_optimizer,
    property_matcher,
)
from bw_tools.modules.bw_pbr_reference import bw_pbr_reference
from bw_tools.modules.bw_framer import bw_framer

from tests import (
    test_chain_dimension,
    test_layout_graph,
    test_node,
    test_node_selection,
    test_straighten_connection,
    test_optimize_graph,
)

modules = [
    bw_optimize_graph,
    optimizer,
    uniform_color_optimizer,
    comp_graph_optimizer,
    atomic_optimizer,
    property_matcher,
    bw_settings,
    bw_settings_dialog,
    bw_settings_model,
    bw_api_tool,
    bw_node,
    bw_node_selection,
    bw_chain_dimension,
    bw_layout_graph,
    node_sorting,
    aligner_vertical,
    alignment_behavior,
    aligner_mainline,
    layout_node,
    bw_straighten_connection,
    straighten_node,
    straighten_behavior,
    bw_pbr_reference,
    bw_framer,
    test_straighten_connection,
    test_layout_graph,
    test_node_selection,
    test_node,
    test_chain_dimension,
    test_optimize_graph,
]


for module in modules:
    print(f"Reloading {str(module)}")
    importlib.reload(module)
