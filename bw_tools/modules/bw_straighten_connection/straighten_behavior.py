from __future__ import annotations

from abc import ABC, abstractmethod
from bw_tools.common.bw_node import Float2
from dataclasses import dataclass
from typing import TypeVar, TYPE_CHECKING
import sd

if TYPE_CHECKING:
    from .straighten_node import StraightenNode

DISTANCE = 96
STRIDE = 21.33  # Magic number between each input slot


@dataclass
class AbstractStraightenBehavior(ABC):
    graph: None

    @abstractmethod
    def get_position_first_dot(
        self,
        source_pos: Float2,
        target_pos: Float2,
        index: int,
    ) -> Float2:
        pass

    @abstractmethod
    def get_position_dot(
        self,
        dot_node: StraightenNode,
        source_pos: Float2,
        target_pos: Float2,
        index: int,
    ) -> Float2:
        pass


class NextToOutput(AbstractStraightenBehavior):
    def get_position_first_dot(
        self,
        source_pos: Float2,
        target_pos: Float2,
        index: int,
    ):
        return Float2(source_pos.x + DISTANCE, source_pos.y + (STRIDE * index))

    def get_position_dot(
        self,
        source_pos: Float2,
        target_pos: Float2,
        index: int,
    ):
        return Float2(target_pos.x - DISTANCE, source_pos.y)


class NextToInput(AbstractStraightenBehavior):
    def straighten_connection_for_property(self, property):
        return super().straighten_connection_for_property(property)
