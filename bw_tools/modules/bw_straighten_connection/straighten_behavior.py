from __future__ import annotations

from abc import ABC, abstractmethod, abstractproperty
from bw_tools.modules.bw_straighten_connection.bw_straighten_connection import StraightenConnectionData
from bw_tools.common.bw_node import Float2
from dataclasses import dataclass
from typing import Dict, TypeVar, TYPE_CHECKING
import sd

if TYPE_CHECKING:
    from .straighten_node import StraightenNode
    from .bw_straighten_connection import BaseDotNodeBounds

DISTANCE = 96
STRIDE = 21.33  # Magic number between each input slot


@dataclass
class AbstractStraightenBehavior(ABC):
    graph: None

    @property
    @abstractmethod
    def delete_base_dot_nodes(self) -> bool:
        pass

    @abstractmethod
    def get_position_first_dot(
        self,
        source_pos: Float2,
        target_pos: Float2,
        index: int,
    ) -> Float2:
        pass

    @abstractmethod
    def get_position_target_dot(
        self,
        dot_node: StraightenNode,
        source_pos: Float2,
        target_pos: Float2,
        index: int,
    ) -> Float2:
        pass

    @abstractmethod
    def align_base_dot_nodes(self, source_node: StraightenNode, data: StraightenConnectionData):
        pass



class NextToOutput(AbstractStraightenBehavior):
    @property
    def delete_base_dot_nodes(self) -> bool:
        return True

    def get_position_first_dot(
        self,
        source_pos: Float2,
        target_pos: Float2,
        index: int,
    ) -> Float2:
        return Float2(source_pos.x + DISTANCE, source_pos.y + (STRIDE * index))

    def get_position_target_dot(
        self,
        source_pos: Float2,
        target_pos: Float2,
        index: int,
    ) -> Float2:
        return Float2(target_pos.x - DISTANCE, source_pos.y)
    
    def align_base_dot_nodes(self, source_node: StraightenNode, data: StraightenConnectionData):
        mid_point = (data.base_dot_nodes_bounds.upper_bound + data.base_dot_nodes_bounds.lower_bound) / 2
        offset = source_node.pos.y - mid_point
        # Position base dot nodes. Move to behavior
        for i, _ in enumerate(source_node.output_connectable_properties):
            if not data.connection[i]:
                continue

            dot_node: StraightenNode = data.base_dot_node[i]
            dot_node.set_position(dot_node.pos.x, dot_node.pos.y + offset)


class NextToInput(AbstractStraightenBehavior):
    def straighten_connection_for_property(self, property):
        return super().straighten_connection_for_property(property)
