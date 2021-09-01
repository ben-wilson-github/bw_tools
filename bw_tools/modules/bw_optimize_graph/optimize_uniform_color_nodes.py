from __future__ import annotations
from bw_tools.common.bw_api_tool import NodeID
from typing import List, TYPE_CHECKING

if TYPE_CHECKING:
    from bw_tools.common.bw_node import Node
    from bw_tools.common.bw_node_selection import NodeSelection


def get_uniform_color_nodes(node_selection: NodeSelection) -> List[Node]:
    return [
        node
        for node in node_selection.nodes
        if node.api_node.getDefinition().getId() != NodeID.UNIFORM_COLOR.value
    ]
