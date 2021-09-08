from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from bw_tools.common.bw_api_tool import NodeID
from sd.api.sdproperty import SDPropertyInheritanceMethod

from . import optimizer

if TYPE_CHECKING:
    from bw_tools.common.bw_node import Node


@dataclass
class UniformOptimizer(optimizer.Optimizer):
    optimized_count = 0

    def run(self):
        uniform_color_nodes = self.get_nodes(NodeID.UNIFORM_COLOR)
        uniform_color_nodes.sort(key=lambda n: n.pos.x)

        for node in uniform_color_nodes:
            self._optimize_output_size(node)
        self.optimized_count = len(uniform_color_nodes)

    def _optimize_output_size(self, node: Node):
        self._set_output_size(node, 4)
        self._set_connected_output_nodes_inheritance_method(
            node, SDPropertyInheritanceMethod.RelativeToParent
        )
