from bw_tools.common.bw_node import Float2
from typing import List, TYPE_CHECKING, Optional
from dataclasses import dataclass, field
from bw_tools.common.bw_node_selection import (
    NodeSelection,
    Node,
)

SPACER = 32

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

    def update_all_chain_positions_deep(self):
        input_node: LayoutNode
        for input_node in self.input_nodes:
            input_node.alignment_behavior.exec()
            if input_node.has_branching_outputs: 
                potential_new_pos = Float2(self.pos.x - (self.width / 2) - SPACER - (input_node.width / 2), input_node.farthest_output_nodes_in_x[0].pos.y)
                if potential_new_pos.x < input_node.pos.x:
                    input_node.set_position(potential_new_pos.x, potential_new_pos.y)
                
                if input_node.alignment_behavior.offset_node is not input_node.farthest_output_nodes_in_x[0]:
                    input_node.alignment_behavior.offset_node = input_node.farthest_output_nodes_in_x[0]
            
                input_node.alignment_behavior.update_offset(input_node.pos)
      
            input_node.update_all_chain_positions_deep()


@dataclass
class LayoutNodeSelection(NodeSelection):
    dot_nodes: List[LayoutNode] = field(
        init=False, default_factory=list, repr=False
    )
    root_nodes: List[LayoutNode] = field(
        init=False, default_factory=list, repr=False
    )
    branching_output_nodes: List[LayoutNode] = field(
        init=False, default_factory=list, repr=False
    )

    def __post_init__(self):
        super().__post_init__()
        self._sort_nodes()

    def _sort_nodes(self):
        for node in self.nodes:
            if node.is_root:
                self.root_nodes.append(node)

            if node.is_dot:
                self.dot_nodes.append(node)

            if node.has_branching_outputs:
                self.branching_output_nodes.append(node)

    def _create_nodes(self):
        for api_node in self.api_nodes:
            node = LayoutNode(api_node)
            self.add_node(node)
