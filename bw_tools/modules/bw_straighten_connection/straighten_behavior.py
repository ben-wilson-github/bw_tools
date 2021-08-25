from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import TYPE_CHECKING

from bw_tools.common.bw_node import Float2

if TYPE_CHECKING:
    from .bw_straighten_connection import (
        StraightenConnectionData,
        StraightenSettings,
    )
    from .straighten_node import StraightenNode


@dataclass
class AbstractStraightenBehavior(ABC):
    graph: None

    @property
    @abstractmethod
    def delete_base_dot_nodes(self) -> bool:
        pass

    @abstractmethod
    def connect_base_dot_nodes(
        self, source_node: StraightenNode, data: StraightenConnectionData
    ) -> bool:
        pass

    @abstractmethod
    def get_position_target_dot(
        self,
        dot_node: StraightenNode,
        source_pos: Float2,
        target_pos: Float2,
        index: int,
        settings: StraightenSettings,
    ) -> Float2:
        pass

    @abstractmethod
    def align_base_dot_nodes(
        self,
        source_node: StraightenNode,
        data: StraightenConnectionData,
    ):
        pass

    @abstractmethod
    def reuse_previous_dot_node(
        self,
        previous_target_node: StraightenNode,
        next_target_node: StraightenNode,
        data: StraightenConnectionData,
        i: int,
        settings: StraightenSettings,
    ) -> bool:
        pass


class BreakAtTarget(AbstractStraightenBehavior):
    @property
    def delete_base_dot_nodes(self) -> bool:
        return True

    def connect_base_dot_nodes(
        self, source_node: StraightenNode, data: StraightenConnectionData
    ) -> bool:
        return (
            source_node.output_connectable_properties_count
            != data.properties_with_outputs_count
        )

    def reuse_previous_dot_node(
        self,
        previous_target_node: StraightenNode,
        next_target_node: StraightenNode,
        data: StraightenConnectionData,
        i: int,
        settings: StraightenSettings,
    ) -> bool:
        return (
            previous_target_node.identifier == next_target_node.identifier
            or data.base_dot_node[i].pos.y == next_target_node.pos.y
            or next_target_node.pos.x - settings.dot_node_distance
            <= previous_target_node.pos.x
        )

    def get_position_target_dot(
        self,
        source_pos: Float2,
        target_pos: Float2,
        index: int,
        settings: StraightenSettings,
    ) -> Float2:
        return Float2(target_pos.x - settings.dot_node_distance, source_pos.y)

    def align_base_dot_nodes(
        self, source_node: StraightenNode, data: StraightenConnectionData
    ):
        mid_point = (
            data.base_dot_nodes_bounds.upper_bound
            + data.base_dot_nodes_bounds.lower_bound
        ) / 2
        offset = source_node.pos.y - mid_point
        for i, _ in enumerate(source_node.output_connectable_properties):
            if not data.connection[i]:
                continue

            dot_node: StraightenNode = data.base_dot_node[i]
            dot_node.set_position(dot_node.pos.x, dot_node.pos.y + offset)


class BreakAtSource(AbstractStraightenBehavior):
    @property
    def delete_base_dot_nodes(self) -> bool:
        return False

    def connect_base_dot_nodes(
        self, source_node: StraightenNode, data: StraightenConnectionData
    ) -> bool:
        return True

    def get_position_target_dot(
        self,
        source_pos: Float2,
        target_pos: Float2,
        index: int,
        settings: StraightenSettings,
    ) -> Float2:
        return Float2(target_pos.x - settings.dot_node_distance, source_pos.y)

    def align_base_dot_nodes(
        self, source_node: StraightenNode, data: StraightenConnectionData
    ):

        for i, _ in enumerate(source_node.output_connectable_properties):
            if not data.connection[i]:
                continue

            mean = sum(
                [
                    con.getInputPropertyNode().getPosition().y
                    for con in data.connection[i]
                    if con
                ]
            ) / len(data.connection[i])

            data.base_dot_node[i].set_position(
                data.base_dot_node[i].pos.x, mean
            )

    def reuse_previous_dot_node(
        self,
        previous_target_node: StraightenNode,
        next_target_node: StraightenNode,
        data: StraightenConnectionData,
        i: int,
        settings: StraightenSettings,
    ) -> bool:
        return (
            previous_target_node.identifier == next_target_node.identifier
            or data.current_source_node[i].pos.y == next_target_node.pos.y
            and len(data.connection[i]) < 2
            or next_target_node.pos.x - settings.dot_node_distance
            <= previous_target_node.pos.x
        )
