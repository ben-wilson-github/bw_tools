from __future__ import annotations

import math
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import TYPE_CHECKING, List

from bw_tools.common.bw_api_tool import SDSBSCompGraph
from bw_tools.common.bw_node import Float2

from .straighten_node import StraightenNode

if TYPE_CHECKING:
    from .bw_straighten_connection import (
        StraightenConnectionData,
        StraightenSettings,
    )

STRIDE = 21.33  # Magic number between each input slot


@dataclass
class AbstractStraightenBehavior(ABC):
    graph: SDSBSCompGraph

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
    def should_create_target_dot_node(
        self,
        source_node: StraightenNode,
        dot_node: StraightenNode,
        target_node: StraightenNode,
        data: StraightenConnectionData,
        i: int,
        settings: StraightenSettings,
    ) -> bool:
        pass

    @abstractmethod
    def get_position_target_dot(
        self,
        source_node: StraightenNode,
        target_node: StraightenNode,
        data: StraightenNode,
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

    def _get_position_of_top_index_in_target(
        self, source_node: StraightenNode, target_node: StraightenNode
    ) -> float:
        offset = (
            self._calculate_mid_point_for_input_connections_in_target_node(
                target_node
            )
        )

        top_index_in_target = source_node.indices_in_target_node(target_node)[
            0
        ]

        return target_node.pos.y + offset + (STRIDE * top_index_in_target)

    def _calculate_mid_point_for_input_connections_in_target_node(
        self, target_node: StraightenNode
    ) -> float:
        lower_bound = target_node.pos.y
        # Stack positions
        for i in range(target_node.input_connectable_properties_count):
            pos = target_node.pos.y + (STRIDE * i)
            lower_bound = max(lower_bound, pos)

        mid_point = (target_node.pos.y + lower_bound) / 2
        return target_node.pos.y - mid_point


class BreakAtTarget(AbstractStraightenBehavior):
    def should_create_base_dot_node(
        self,
        source_node: StraightenNode,
        data: StraightenConnectionData,
        i: int,
        settings: StraightenSettings,
    ) -> bool:
        potential_pos = source_node.pos.x + settings.dot_node_distance
        output_node = data.output_nodes[i][0]
        limit = output_node.pos.x - settings.dot_node_distance

        if potential_pos >= limit:
            return False

        if (
            source_node.output_connectable_properties_count
            == data.properties_with_outputs_count
        ):
            return False

        if any(
            output_node.pos.y == source_node.pos.y
            for output_node in data.output_nodes[i]
        ):
            return False
        else:
            return True

    def should_create_target_dot_node(
        self,
        source_node: StraightenNode,
        dot_node: StraightenNode,
        target_node: StraightenNode,
        data: StraightenConnectionData,
        i: int,
        settings: StraightenSettings,
    ) -> bool:
        potential_pos = dot_node.pos.x + settings.dot_node_distance
        limit = target_node.pos.x - settings.dot_node_distance
        if potential_pos >= limit:
            return False

        pos_y_output_index = dot_node.get_position_of_output_index(i)
        pos_y_input_index = self._get_position_of_top_index_in_target(
            source_node, target_node
        )

        if math.isclose(pos_y_output_index, pos_y_input_index):
            return False
        else:
            return True

    def get_position_target_dot(
        self,
        source_node: StraightenNode,
        target_node: StraightenNode,
        data: StraightenConnectionData,
        i: int,
        settings: StraightenSettings,
    ) -> Float2:
        if source_node.is_dot:
            return Float2(
                target_node.pos.x - settings.dot_node_distance,
                source_node.pos.y,
            )

        lower_bound = source_node.pos.y
        stack_index = 0
        pos = dict()
        for j in range(source_node.output_connectable_properties_count):
            pos[j] = source_node.pos.y + (STRIDE * stack_index)
            lower_bound = max(lower_bound, pos[j])
            stack_index += 1

        mid_point = (source_node.pos.y + lower_bound) / 2
        offset = source_node.pos.y - mid_point
        return Float2(
            target_node.pos.x - settings.dot_node_distance, pos[i] + offset
        )

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


class BreakAtSource(AbstractStraightenBehavior):
    def should_create_base_dot_node(
        self,
        source_node: StraightenNode,
        data: StraightenConnectionData,
        i: int,
        settings: StraightenSettings,
    ) -> bool:
        potential_pos = source_node.pos.x + settings.dot_node_distance
        # Should only create if some of the output nodes are far
        # enough away to be able to connect to the newly created
        # dot node
        output_nodes_in_front = [
            output_node
            for output_node in data.output_nodes[i]
            if output_node.pos.x >= potential_pos + settings.dot_node_distance
        ]
        if len(output_nodes_in_front) == 0:
            return False

        limit = output_nodes_in_front[0].pos.x
        if potential_pos >= limit:
            return False

        if len(output_nodes_in_front) == 1:
            output_node = output_nodes_in_front[0]

            pos_y_output_index = source_node.get_position_of_output_index(i)
            pos_y_input_index = self._get_position_of_top_index_in_target(
                source_node, output_node
            )
            if math.isclose(pos_y_output_index, pos_y_input_index):
                return False
            else:
                return True

        if len(output_nodes_in_front) >= 2:
            mid_point = self._calculate_mid_point_from_output_nodes(
                source_node, output_nodes_in_front, data, i, settings
            )
            if mid_point == source_node.pos.y:
                return False
            else:
                return True

    def should_create_target_dot_node(
        self,
        source_node: StraightenNode,
        dot_node: StraightenNode,
        target_node: StraightenNode,
        data: StraightenConnectionData,
        i: int,
        settings: StraightenSettings,
    ) -> bool:
        potential_pos = dot_node.pos.x + settings.dot_node_distance
        limit = target_node.pos.x - settings.dot_node_distance
        if potential_pos >= limit:
            return False

        output_nodes_in_front = [
            output_node
            for output_node in data.output_nodes[i]
            if output_node.pos.x >= potential_pos + settings.dot_node_distance
        ]

        if len(output_nodes_in_front) == 0:
            return False

        if len(output_nodes_in_front) == 1:
            if not dot_node.is_dot:
                pos_y_output_index = dot_node.get_position_of_output_index(i)
            else:
                pos_y_output_index = dot_node.pos.y
            pos_y_input_index = self._get_position_of_top_index_in_target(
                source_node, output_nodes_in_front[0]
            )
            if math.isclose(pos_y_output_index, pos_y_input_index):
                return False
            else:
                return True
        return True

    def get_position_target_dot(
        self,
        source_node: StraightenNode,
        target_node: StraightenNode,
        data: StraightenConnectionData,
        i: int,
        settings: StraightenSettings,
    ) -> Float2:
        return Float2(
            target_node.pos.x - settings.dot_node_distance, source_node.pos.y
        )

    def align_base_dot_node(
        self,
        source_node: StraightenNode,
        data: StraightenConnectionData,
        i: int,
        settings: StraightenSettings,
    ) -> None:

        output_nodes_in_front = [
            output_node
            for output_node in data.output_nodes[i]
            if output_node.pos.x
            >= source_node.pos.x + settings.dot_node_distance * 2
        ]

        if len(output_nodes_in_front) == 1:
            pos_y = self._get_position_of_top_index_in_target(
                source_node, output_nodes_in_front[0]
            )

            data.base_dot_node[i].set_position(
                data.base_dot_node[i].pos.x,
                pos_y,
            )

        else:  # multiple output nodes
            mid_point = self._calculate_mid_point_from_output_nodes(
                source_node, output_nodes_in_front, data, i, settings
            )
            data.base_dot_node[i].set_position(
                data.base_dot_node[i].pos.x, mid_point
            )

    def _calculate_mid_point_from_output_nodes(
        self,
        source_node: StraightenNode,
        output_nodes: List[StraightenNode],
        data: StraightenConnectionData,
        i: int,
        settings: StraightenSettings,
    ) -> float:
        if len(output_nodes) == 1:
            return output_nodes[0].pos.y

        output_nodes.sort(key=lambda n: n.pos.y)
        upper_bound = output_nodes[0].pos.y
        lower_bound = output_nodes[-1].pos.y
        return (upper_bound + lower_bound) / 2
