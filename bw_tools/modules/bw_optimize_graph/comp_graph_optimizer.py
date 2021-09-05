from __future__ import annotations, unicode_literals

from dataclasses import dataclass
from typing import TYPE_CHECKING, List

from bw_tools.common.bw_api_tool import NodeID
from sd.api.sdproperty import SDPropertyInheritanceMethod

from . import optimizer

if TYPE_CHECKING:
    from bw_tools.common.bw_node import Node


@dataclass
class CompGraphOptimizer(optimizer.Optimizer):
    def run(self):
        comp_nodes = self.get_nodes(NodeID.COMP_GRAPH)
        comp_nodes.sort(key=lambda n: n.pos.x)

        node_dict = self.find_duplicates(comp_nodes)
        self.delete_duplicate_nodes(node_dict)
