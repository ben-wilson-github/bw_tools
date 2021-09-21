from dataclasses import dataclass, field
from typing import List, Optional

from common.bw_node_selection import BWNode, BWNodeSelection
from sd.api import sdbasetypes

from .alignment_behavior import BWNodeAlignmentBehavior


@dataclass
class BWLayoutNode(BWNode):
    _alignment_behavior: Optional[BWNodeAlignmentBehavior] = field(
        init=False, repr=False, default=None
    )

    @property
    def alignment_behavior(self) -> BWNodeAlignmentBehavior:
        return self._alignment_behavior

    @alignment_behavior.setter
    def alignment_behavior(self, behavior: BWNodeAlignmentBehavior):
        self._alignment_behavior = behavior
        self._alignment_behavior._parent = self

    @property
    def closest_output_node_in_x(self) -> Optional["BWLayoutNode"]:
        if self.is_root:
            return None

        closest = self.output_nodes[0]
        for output_node in self.output_nodes:
            if output_node.pos.x < closest.pos.x:
                closest = output_node
        return closest

    @property
    def farthest_output_nodes_in_x(self) -> Optional[List["BWLayoutNode"]]:
        if self.is_root:
            return None
        farthest = [self.output_nodes[0]]

        output_node: "BWLayoutNode"
        for output_node in self.output_nodes[1:]:
            if output_node.pos.x > farthest[0].pos.x:
                farthest = [output_node]
            elif output_node.pos.x == farthest[0].pos.x:
                farthest.append(output_node)

        if len(farthest) >= 2:
            farthest.sort(key=lambda x: x.pos.y)
        return farthest

    def set_position(self, x, y):
        self.pos.x = x
        self.pos.y = y

    def set_api_position(self):
        self.api_node.setPosition(sdbasetypes.float2(self.pos.x, self.pos.y))

    def update_all_chain_positions(self):
        input_node: BWLayoutNode
        for input_node in self.input_nodes:
            if input_node.alignment_behavior.offset_node is not self:
                continue

            input_node.alignment_behavior.exec()
            input_node.update_all_chain_positions()


@dataclass
class BWLayoutNodeSelection(BWNodeSelection):
    dot_nodes: List[BWLayoutNode] = field(
        init=False, default_factory=list, repr=False
    )
    root_nodes: List[BWLayoutNode] = field(
        init=False, default_factory=list, repr=False
    )
    branching_output_nodes: List[BWLayoutNode] = field(
        init=False, default_factory=list, repr=False
    )
    branching_input_nodes: List[BWLayoutNode] = field(
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

            if (
                node.has_branching_outputs
                and node not in self.branching_output_nodes
            ):
                self.branching_output_nodes.append(node)

            if (
                node.has_branching_inputs
                and node not in self.branching_input_nodes
            ):
                self.branching_input_nodes.append(node)

    def _create_nodes(self):
        for api_node in self.api_nodes:
            node = BWLayoutNode(api_node)
            self.add_node(node)
