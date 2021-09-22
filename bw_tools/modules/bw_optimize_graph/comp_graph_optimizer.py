from dataclasses import dataclass

from bw_tools.common.bw_api_tool import CompNodeID

from .optimizer import Optimizer


@dataclass
class CompGraphOptimizer(Optimizer):
    def run(self):
        comp_nodes = self.get_nodes(CompNodeID.COMP_GRAPH)
        comp_nodes.sort(key=lambda n: n.pos.x)

        node_dict = self.find_duplicates(comp_nodes)
        self.delete_duplicate_nodes(node_dict)
