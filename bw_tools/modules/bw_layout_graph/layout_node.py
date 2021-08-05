from dataclasses import dataclass
from bw_tools.common.bw_node_selection import NodeSelection, Node


@dataclass
class LayoutNode(Node):
    pass


@dataclass
class LayoutNodeSelection(NodeSelection):
    def _create_nodes(self):
        for api_node in self.api_nodes:
            node = LayoutNode(api_node)
            self.add_node(node)
