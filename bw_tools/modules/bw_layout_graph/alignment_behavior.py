from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Tuple


from bw_tools.common.bw_node import Float2

if TYPE_CHECKING:
    from .layout_node import LayoutNode

SPACER = 32


@dataclass
class NodeAlignmentBehavior(ABC):
    _parent: LayoutNode = field(repr=False)
    offset: Float2 = field(default_factory=Float2)
    offset_node: LayoutNode = field(init=False)

    def __post_init__(self):
        self.offset_node = self._parent

    @abstractmethod
    def exec(self):
        pass

    @abstractmethod
    def update_offset(self, new_post: Float2):
        pass


@dataclass
class StaticAlignment(NodeAlignmentBehavior):
    def exec(self):
        self._parent.set_position(
            self.offset_node.pos.x + self.offset.x,
            self.offset_node.pos.y + self.offset.y,
        )

    def update_offset(self, new_pos: Float2):
        self.offset.x = new_pos.x - self.offset_node.pos.x
        self.offset.y = new_pos.y - self.offset_node.pos.y


@dataclass
class PostAlignmentBehavior(ABC):
    @abstractmethod
    def exec(self, node: LayoutNode):
        pass

    @staticmethod
    def calculate_mid_point(
        a: LayoutNode, b: LayoutNode
    ) -> Tuple[float, float]:
        x = (a.pos.x + b.pos.x) / 2
        y = (a.pos.y + b.pos.y) / 2

        return x, y


# TODO: Add offset abstract method
@dataclass
class VerticalAlignMidPoint(PostAlignmentBehavior):
    def exec(self, node: LayoutNode):
        _, mid_point = self.calculate_mid_point(
            node.input_nodes[0], node.input_nodes[-1]
        )
        offset = node.pos.y - mid_point

        input_node: LayoutNode
        for input_node in node.input_nodes:
            if node is not input_node.alignment_behavior.offset_node:
                # Same as resetting its position
                input_node.alignment_behavior.exec()
                # Remove the node that would have been there
                # for all input_nodes after this
                offset -= input_node.height + SPACER
            else:
                input_node.alignment_behavior.offset_node = node
                input_node.alignment_behavior.update_offset(
                    Float2(input_node.pos.x, input_node.pos.y + offset)
                )
                input_node.alignment_behavior.exec()

            input_node.update_all_chain_positions()


@dataclass
class VerticalAlignFarthestInput(PostAlignmentBehavior):
    def exec(self, node: LayoutNode):
        farthest = [node.input_nodes[0]]
        input_node: LayoutNode
        for input_node in node.input_nodes[1:]:
            if input_node.pos.x < farthest[0].pos.x:
                farthest = [input_node]
            elif input_node.pos.x == farthest[0].pos.x:
                farthest.append(input_node)

        if len(farthest) > 1:
            mid_point_align = VerticalAlignMidPoint()
            mid_point_align.exec(node)
            return

        farthest = farthest[0]
        offset = node.pos.y - farthest.pos.y

        input_node: LayoutNode
        for input_node in node.input_nodes:
            if node is not input_node.alignment_behavior.offset_node:
                # Same as resetting its position
                input_node.alignment_behavior.exec()
                offset -= input_node.height + SPACER
            else:
                input_node.alignment_behavior.offset_node = node
                input_node.alignment_behavior.update_offset(
                    Float2(input_node.pos.x, input_node.pos.y + offset)
                )
                input_node.alignment_behavior.exec()

            input_node.update_all_chain_positions()


@dataclass
class VerticalAlignTopStack(PostAlignmentBehavior):
    def exec(self, node: LayoutNode):
        input_node: LayoutNode
        for input_node in node.input_nodes:
            if node is not input_node.alignment_behavior.offset_node:
                input_node.alignment_behavior.exec()
            else:
                input_node.alignment_behavior.offset_node = node
                input_node.alignment_behavior.update_offset(input_node.pos)
                input_node.alignment_behavior.exec()

            input_node.update_all_chain_positions()
