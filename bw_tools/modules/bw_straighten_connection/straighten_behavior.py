from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import TypeVar, TYPE_CHECKING
import sd
if TYPE_CHECKING:
    from .straighten_node import StraightenNode


@dataclass
class AbstractStraightenBehavior(ABC):
    graph: None

    @abstractmethod
    def straighten_connection_for_property(
        self, input_node, prop
    ):
        pass

    def insert_dot_node(
        self, source_node, target_node
    ):
        dot_node = self.graph.newNode("sbs::compositing::passthrough")

        x = (source_node.pos.x + target_node.pos.x) / 2
        y = (source_node.pos.y + target_node.pos.y) / 2
        dot_node.setPosition(sd.api.sdbasetypes.float2(x, y))
        return dot_node


class NextToOutput(AbstractStraightenBehavior):
    def straighten_connection_for_property(
        self, input_node, prop
    ):
        pass


class NextToInput(AbstractStraightenBehavior):
    def straighten_connection_for_property(self, property):
        return super().straighten_connection_for_property(property)
