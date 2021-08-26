from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import TYPE_CHECKING, List

from bw_tools.common.bw_node import Float2
from .straighten_node import StraightenNode

if TYPE_CHECKING:
    from .bw_straighten_connection import (
        StraightenConnectionData,
        StraightenSettings,
    )
    from bw_tools.common.bw_api_tool import SDNode
    


class NoOutputNodes(Exception):
    pass


@dataclass
class AbstractStraightenBehavior(ABC):
    graph: None

    @abstractmethod
    def should_create_base_dot_node(
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
    def should_delete_base_dot_node(
        self,
        source_node: StraightenNode,
        data: StraightenConnectionData,
        i: int,
        settings: StraightenSettings,
    ):
        pass


class BreakAtTarget(AbstractStraightenBehavior):
    def should_delete_base_dot_node(
        self,
        source_node: StraightenNode,
        data: StraightenConnectionData,
        i: int,
        settings: StraightenSettings,
    ):
        target_node = StraightenNode(
            data.connection[i][0].getInputPropertyNode(), source_node.graph
        )
        return self.should_create_target_dot_node(data.base_dot_node[i], target_node, data, i, settings)

    REMOVE TARGET NODES IF THEY ARE INLINE. IF CONNECTS TO MIDDLE INDEX?

    def get_position_target_dot(
        self,
        source_pos: Float2,
        target_pos: Float2,
        index: int,
        settings: StraightenSettings,
    ) -> Float2:
        return Float2(target_pos.x - settings.dot_node_distance, source_pos.y)

    def _calculate_offset(
        self, source_node: StraightenNode, data: StraightenConnectionData
    ) -> float:
        base_root_nodes = [
            data.base_dot_node[j]
            for j in range(source_node.output_connectable_properties_count)
            if data.base_dot_node[j] is not None
        ]
        mid_point = (source_node.pos.y + base_root_nodes[-1].pos.y) / 2
        return source_node.pos.y - mid_point

    def align_base_dot_node(
        self,
        source_node: StraightenNode,
        data: StraightenConnectionData,
        i: int,
        settings: StraightenSettings,
    ):
        data.base_dot_node[i].set_position(
            data.base_dot_node[i].pos.x,
            data.base_dot_node[i].pos.y
            + self._calculate_offset(source_node, data),
        )

    def should_create_base_dot_node(
        self,
        source_node: StraightenNode,
        data: StraightenConnectionData,
        i: int,
        settings: StraightenSettings,
    ) -> bool:
        return (
            data.connection[i][0].getInputPropertyNode().getPosition().x
            >= source_node.pos.x + settings.dot_node_distance * 2
        )

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
        )


class BreakAtSource(AbstractStraightenBehavior):
    def should_delete_base_dot_node(
        self,
        source_node: StraightenNode,
        data: StraightenConnectionData,
        i: int,
        settings: StraightenSettings,
    ):
        return False

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

    def should_create_base_dot_node(
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
