from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import TYPE_CHECKING, List

from bw_tools.common.bw_node import Float2

if TYPE_CHECKING:
    from .bw_straighten_connection import (
        StraightenConnectionData,
        StraightenSettings,
    )
    from bw_tools.common.bw_api_tool import SDNode
    from .straighten_node import StraightenNode


class NoOutputNodes(Exception):
    pass


@dataclass
class AbstractStraightenBehavior(ABC):
    graph: None

    @abstractmethod
    def should_add_base_dot_node(
        self,
        source_node: StraightenNode,
        data: StraightenConnectionData,
        i: int,
        settings: StraightenSettings,
    ) -> bool:
        pass

    @abstractmethod
    def should_connect_node(
        self,
        source_node: StraightenNode,
        target_node: StraightenNode,
        data: StraightenConnectionData,
        i: int,
        settings: StraightenSettings,
    ) -> bool:
        pass

    @abstractmethod
    def delete_base_dot_node(
        self,
        source_node: StraightenNode,
        data: StraightenConnectionData,
        i: int,
        settings: StraightenSettings,
    ) -> bool:
        pass

    @abstractmethod
    def should_create_target_dot_node(
        self,
        previous_target_node: StraightenNode,
        next_target_node: StraightenNode,
        data: StraightenConnectionData,
        i: int,
        settings: StraightenSettings,
    ) -> bool:
        pass

    @abstractmethod
    def connect_base_dot_node(
        self,
        source_node: StraightenNode,
        data: StraightenConnectionData,
        i: int,
        settings: StraightenSettings,
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
    def align_base_dot_node(
        self,
        source_node: StraightenNode,
        data: StraightenConnectionData,
        i: int,
        settings: StraightenSettings,
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
        self,
        source_node: StraightenNode,
        data: StraightenConnectionData,
        i: int,
        settings: StraightenSettings,
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
            or next_target_node.pos.x
            - settings.dot_node_distance
            - next_target_node.width
            <= data.current_source_node[i].pos.x
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
    def _calculate_mean_from_output_nodes(
        self,
        source_node: StraightenNode,
        data: StraightenConnectionData,
        i: int,
        settings: StraightenSettings,
    ) -> float:
        connections = data.connection[i]

        # Remove target nodes too close
        target_nodes = [
            con.getInputPropertyNode()
            for con in connections
            if con.getInputPropertyNode().getPosition().x
            > source_node.pos.x + settings.dot_node_distance * 2
        ]
        if not target_nodes:
            raise NoOutputNodes

        if len(target_nodes) == 1:
            return target_nodes[0].getPosition().y

        target_nodes.sort(key=lambda n: n.getPosition().y)
        upper_bound = target_nodes[0].getPosition().y
        lower_bound = target_nodes[-1].getPosition().y
        return (upper_bound + lower_bound) / 2

    def should_connect_node(
        self,
        source_node: StraightenNode,
        target_node: StraightenNode,
        data: StraightenConnectionData,
        i: int,
        settings: StraightenSettings,
    ) -> bool:
        return (
            target_node.pos.x >= source_node.pos.x + settings.dot_node_distance
        )

    def should_add_base_dot_node(
        self,
        source_node: StraightenNode,
        data: StraightenConnectionData,
        i: int,
        settings: StraightenSettings,
    ):
        try:
            mean_y = self._calculate_mean_from_output_nodes(
                source_node, data, i, settings
            )
        except NoOutputNodes:
            return False

        return mean_y != source_node.pos.y

    def should_create_target_dot_node(
        self,
        dot_node: StraightenNode,
        target_node: StraightenNode,
        data: StraightenConnectionData,
        i: int,
        settings: StraightenSettings,
    ) -> bool:
        return (
            target_node.pos.x
            > dot_node.pos.x + settings.dot_node_distance + target_node.width
            and len(data.connection[i]) > 1
            or target_node.pos.y != dot_node.pos.y
        )

    def delete_base_dot_node(
        self,
        source_node: StraightenNode,
        data: StraightenConnectionData,
        i: int,
        settings: StraightenSettings,
    ) -> bool:
        target_node = data.connection[i][0].getInputPropertyNode()
        return (
            target_node.getPosition().x
            < data.base_dot_node[i].pos.x + settings.dot_node_distance
            or data.base_dot_node[i].pos.y == source_node.pos.y
        )

    def connect_base_dot_node(
        self,
        source_node: StraightenNode,
        data: StraightenConnectionData,
        i: int,
        settings: StraightenSettings,
    ) -> bool:
        target_node = data.connection[i][0].getInputPropertyNode()
        return (
            target_node.getPosition().x
            > data.base_dot_node[i].pos.x + settings.dot_node_distance
            and data.base_dot_node[i].pos.y != source_node.pos.y
        )

    def get_position_target_dot(
        self,
        source_pos: Float2,
        target_pos: Float2,
        index: int,
        settings: StraightenSettings,
    ) -> Float2:
        return Float2(target_pos.x - settings.dot_node_distance, source_pos.y)

    def align_base_dot_node(
        self,
        source_node: StraightenNode,
        data: StraightenConnectionData,
        i: int,
        settings: StraightenSettings,
    ) -> None:
        try:
            mean_y = self._calculate_mean_from_output_nodes(
                source_node, data, i, settings
            )
        except NoOutputNodes:
            data.base_dot_node[i].set_position(
                data.base_dot_node[i].pos.x, source_node.pos.y
            )
        else:
            data.base_dot_node[i].set_position(
                data.base_dot_node[i].pos.x,
                mean_y,
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
            or next_target_node.pos.x
            - settings.dot_node_distance
            - next_target_node.width
            <= data.current_source_node[i].pos.x
            or data.current_source_node[i].pos.y == next_target_node.pos.y
            and len(data.connection[i]) < 2
        )
