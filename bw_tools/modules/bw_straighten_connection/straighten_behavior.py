from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import TypeVar, TYPE_CHECKING
import sd

if TYPE_CHECKING:
    from .straighten_node import StraightenNode

DISTANCE = 96
STRIDE = 20.8


@dataclass
class AbstractStraightenBehavior(ABC):
    graph: None

    @abstractmethod
    def position_first_dot(
        self,
        dot_node: StraightenNode,
        source_node: StraightenNode,
        target_node: StraightenNode,
        index: int,
    ):
        pass

    @abstractmethod
    def position_dot(
        self,
        dot_node: StraightenNode,
        source_node: StraightenNode,
        target_node: StraightenNode,
        index: int,
    ):
        pass


class NextToOutput(AbstractStraightenBehavior):
    def position_first_dot(
        self,
        dot_node: StraightenNode,
        source_node: StraightenNode,
        target_node: StraightenNode,
        index: int,
    ):
        dot_node.set_position(
            source_node.pos.x + DISTANCE, source_node.pos.y + (STRIDE * index)
        )

    def position_dot(
        self,
        dot_node: StraightenNode,
        source_node: StraightenNode,
        target_node: StraightenNode,
        index: int,
    ):
        dot_node.set_position(
            target_node.pos.x - DISTANCE, source_node.pos.y
        )


class NextToInput(AbstractStraightenBehavior):
    def straighten_connection_for_property(self, property):
        return super().straighten_connection_for_property(property)
