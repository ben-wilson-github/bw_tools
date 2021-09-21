from __future__ import annotations, unicode_literals

from dataclasses import dataclass
from typing import List

from sd.api.sdproperty import SDPropertyCategory

from . import optimizer

# if TYPE_CHECKING:
from bw_tools.common.bw_node import BWNode


@dataclass
class AtomicOptimizer(optimizer.Optimizer):
    def run(self):
        atmoic_nodes = self.get_nodes()
        atmoic_nodes.sort(key=lambda n: n.pos.x)

        node_dict = self.find_duplicates(atmoic_nodes)
        self.delete_duplicate_nodes(node_dict)

    def get_nodes(self) -> List[BWNode]:
        return [
            node
            for node in self.node_selection.nodes
            if node.api_node.getPropertyFromId(
                "unique_filter_output", SDPropertyCategory.Output
            )
            is not None
        ]
