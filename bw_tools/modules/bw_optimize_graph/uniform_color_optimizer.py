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
    duplicate_node_count: int = 0

    def run(self):
        uniform_color_nodes = self._get_uniform_color_nodes()
        uniform_color_nodes.sort(key=lambda n: n.pos.x)
        node_dict = self._find_duplicates(uniform_color_nodes)
        for identifier, duplicate_nodes in node_dict.items():
            # Keep track of duplicate nodes for displaying infor
            # to user
            self.duplicate_node_count += len(duplicate_nodes)

            unique_node = self.node_selection.node(identifier)
            for duplicate_node in duplicate_nodes:
                self._reconnect_output_connections(duplicate_node, unique_node)
                self.node_selection.api_graph.deleteNode(
                    duplicate_node.api_node
                )

            self._optimize_output_size(unique_node)

    def _get_uniform_color_nodes(self) -> List[Node]:
        return [
            node
            for node in self.node_selection.nodes
            if node.api_node.getDefinition().getId()
            == NodeID.UNIFORM_COLOR.value
        ]

    def _optimize_output_size(self, node: Node):
        self._set_output_size(node, 4)
        self._set_connected_output_nodes_inheritance_method(
            node, SDPropertyInheritanceMethod.RelativeToParent
        )
