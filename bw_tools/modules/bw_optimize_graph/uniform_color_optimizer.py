from __future__ import annotations, unicode_literals

from dataclasses import dataclass
from typing import TYPE_CHECKING, List

from bw_tools.common.bw_api_tool import NodeID
from sd.api.sdproperty import SDPropertyInheritanceMethod

from . import optimizer

if TYPE_CHECKING:
    from bw_tools.common.bw_node import Node


@dataclass
class UniformOptimizer(optimizer.Optimizer):
    def run(self):
        uniform_color_nodes = self.get_nodes(NodeID.UNIFORM_COLOR)
        uniform_color_nodes.sort(key=lambda n: n.pos.x)

        node_dict = self.find_duplicates(uniform_color_nodes)
        self.delete_duplicate_nodes(node_dict)

        for identifier, _ in node_dict.items():
            unique_node = self.node_selection.node(identifier)
            self._optimize_output_size(unique_node)

    def _optimize_output_size(self, node: Node):
        self._set_output_size(node, 4)
        self._set_connected_output_nodes_inheritance_method(
            node, SDPropertyInheritanceMethod.RelativeToParent
        )
