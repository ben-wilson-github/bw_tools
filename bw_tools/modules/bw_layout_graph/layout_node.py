from typing import List, TYPE_CHECKING, Optional
from dataclasses import dataclass, field
from bw_tools.common.bw_node_selection import (
    NodeSelection,
    Node,
)


from .alignment_behavior import NodeAlignmentBehavior


@dataclass
class LayoutNode(Node):
    _alignment_behavior: Optional[NodeAlignmentBehavior] = field(
        init=False, repr=False, default=None
    )

    @property
    def alignment_behavior(self) -> NodeAlignmentBehavior:
        return self._alignment_behavior

    @alignment_behavior.setter
    def alignment_behavior(self, behavior: NodeAlignmentBehavior):
        self._alignment_behavior = behavior
        self._alignment_behavior._parent = self

    @property
    def closest_output_node_in_x(self) -> Optional['LayoutNode']:
        if self.is_root:
            return None

        closest = self.output_nodes[0]
        for output_node in self.output_nodes:
            if output_node.pos.x < closest.pos.x:
                closest = output_node
        return closest

    @property
    def farthest_output_nodes_in_x(self) -> Optional[List['LayoutNode']]:
        if self.is_root:
            return None
        farthest = [self.output_nodes[0]]

        output_node: 'LayoutNode'
        for output_node in self.output_nodes[1:]:
            if output_node.pos.x > farthest[0].pos.x:
                farthest = [output_node]
            elif output_node.pos.x == farthest[0].pos.x:
                farthest.append(output_node)

        if len(farthest) >= 2:
            farthest.sort(key=lambda x: x.pos.y)
        return farthest

    def update_all_chain_positions(self):
        input_node: LayoutNode
        for input_node in self.input_nodes:
            if input_node.alignment_behavior.offset_node is not self:
                continue

            input_node.alignment_behavior.exec()
            input_node.update_all_chain_positions()


@dataclass
class LayoutNodeSelection(NodeSelection):
    dot_nodes: List[LayoutNode] = field(
        init=False, default_factory=list, repr=False
    )
    root_nodes: List[LayoutNode] = field(
        init=False, default_factory=list, repr=False
    )

    def __post_init__(self):
        super().__post_init__()
        self._sort_nodes()

    def _create_nodes(self):
        for api_node in self.api_nodes:
            node = LayoutNode(api_node)
            self.add_node(node)
