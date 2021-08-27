from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from os import stat
from pathlib import PosixPath
from typing import TYPE_CHECKING, List
import math

from bw_tools.common.bw_node import Float2
from .straighten_node import StraightenNode

if TYPE_CHECKING:
    from .bw_straighten_connection import (
        StraightenConnectionData,
        StraightenSettings,
    )
    from bw_tools.common.bw_api_tool import SDNode

STRIDE = 21.33  # Magic number between each input slot


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

    # @abstractmethod
    # def should_connect_base_node(
    #     self,
    #     source_node: StraightenNode,
    #     target_node: StraightenNode,
    #     data: StraightenConnectionData,
    #     i: int,
    #     settings: StraightenSettings
    # ) -> bool:
    #     pass

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

    @abstractmethod
    def should_delete_base_dot_node(
        self,
        source_node: StraightenNode,
        data: StraightenConnectionData,
        i: int,
        settings: StraightenSettings,
    ):
        pass

    @staticmethod
    def far_enough_away(
        input_node: StraightenNode,
        output_node: StraightenNode,
        settings: StraightenSettings,
    ):
        return (
            output_node.pos.x
            >= input_node.pos.x + settings.dot_node_distance# * 2
        )


class BreakAtTarget(AbstractStraightenBehavior):
    def should_delete_base_dot_node(
        self,
        source_node: StraightenNode,
        data: StraightenConnectionData,
        i: int,
        settings: StraightenSettings,
    ):
        return False

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
        target_node = StraightenNode(
            data.connection[i][0].getInputPropertyNode(), source_node.graph
        )
        return (
            source_node.output_connectable_properties_count
            != data.properties_with_outputs_count
            and target_node.pos.x
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
        if target_node.pos.x < dot_node.pos.x + settings.dot_node_distance * 2:
            return False

        output_nodes_in_front = [
            StraightenNode(con.getInputPropertyNode(), dot_node.graph)
            for con in data.connection[i]
            if con.getInputPropertyNode().getPosition().x
            > dot_node.pos.x + settings.dot_node_distance * 2
        ]
        output_nodes_in_front = dot_node.output_nodes_in_front(settings)

        if any(
            output_node.pos.y != dot_node.pos.y
            for output_node in output_nodes_in_front
        ):
            return True

        if len(output_nodes_in_front) == 1:
            if target_node.center_index in dot_node.indices_in_target_node(
                target_node
            ):
                return False
        return True


class BreakAtSource(AbstractStraightenBehavior):
    def should_delete_base_dot_node(
        self,
        source_node: StraightenNode,
        data: StraightenConnectionData,
        i: int,
        settings: StraightenSettings,
    ):
        return False

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

    def should_connect_node(
        self,
        source_node: StraightenNode,
        target_node: StraightenNode,
        data: StraightenConnectionData,
        i: int,
        settings: StraightenSettings,
    ) -> bool:

        return target_node.pos.x >= source_node.pos.x + settings.dot_node_distance * 2
        return (
            target_node.pos.x >= source_node.pos.x + settings.dot_node_distance
        )

    def _get_position_of_output_index(self, source_node: StraightenNode, i: int):
        # TODO: Move to node class
        lower_bound = source_node.pos.y
        for j in range(source_node.output_connectable_properties_count):
            lower_bound = max(source_node.pos.y + (STRIDE * j), lower_bound)
        mid_point = (source_node.pos.y + lower_bound) / 2
        offset = source_node.pos.y - mid_point
        return source_node.pos.y + offset + (STRIDE * i)


    def should_create_base_dot_node(
        self,
        source_node: StraightenNode,
        data: StraightenConnectionData,
        i: int,
        settings: StraightenSettings,
    ):
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

            pos_y_output_index = self._get_position_of_output_index(source_node, i)
            pos_y_input_index = self._get_position_of_top_index_in_target(source_node, output_node)
            if math.isclose(pos_y_output_index, pos_y_input_index):
                return False
            else:
                return True

            # indices_in_target = source_node.indices_in_target_node(output_node)
            # if len(indices_in_target) == 1:
            #     index_pos = self._get_position_of_top_index_in_target(
            #         source_node, output_node
            #     )
            #     if source_node.pos.y == index_pos:
            #         return False
            #     else:
            #         return True
            
            # else:   # connects to multiple indices
            #     if source_node.pos.y == output_node.pos.y:
            #         return True
            #     else:
            #         return False
        
        if len(output_nodes_in_front) >= 2:
            mid_point = self._calculate_mid_point_from_output_nodes(
                source_node, output_nodes_in_front, data, i, settings
            )
            if mid_point == source_node.pos.y:
                return False
            else:
                return True
            # if mid_point == source_node.pos.y:
            #     if not source_node.conntects_to_center_index_of_target(
            #         output_nodes_in_front[0]
            #     ):
            #         return True
            #     else:
            #         return False
            # else:
            #     return True

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
                pos_y_output_index = self._get_position_of_output_index(dot_node, i)
            else:
                pos_y_output_index = dot_node.pos.y
            pos_y_input_index = self._get_position_of_top_index_in_target(source_node, output_nodes_in_front[0])
            if math.isclose(pos_y_output_index, pos_y_input_index):
                return False
            else:
                return True
            
        return True

        if len(dot_node.indices_in_target_node(output_nodes_in_front[0])) > 1:
            return True

        if len(output_nodes_in_front) == 1:
            pos_y = self._get_position_of_top_index_in_target(
                dot_node, output_nodes_in_front[0]
            )
            if math.isclose(pos_y, dot_node.pos.y):
                return False
            else:
                return True
        else:
            return True

        # if len(output_nodes_in_front) > 1:
        #     return True

        # if target_node.pos.y != dot_node.pos.y:
        #     return True

        return False

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

    def _get_position_of_top_index_in_target(
        self, source_node: StraightenNode, target_node: StraightenNode
    ):
        offset = (
            self._calculate_mid_point_for_input_connections_in_target_node(
                target_node
            )
        )

        top_index_in_target = source_node.indices_in_target_node(target_node)[
            0
        ]

        return target_node.pos.y + offset + (STRIDE * top_index_in_target)

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
            if output_node.pos.x >= source_node.pos.x + settings.dot_node_distance * 2
        ]

        if len(output_nodes_in_front) == 1:
            pos_y = self._get_position_of_top_index_in_target(
                source_node, output_nodes_in_front[0]
            )

            data.base_dot_node[i].set_position(
                data.base_dot_node[i].pos.x,
                pos_y,
            )

        else:   # multiple output nodes
            mid_point = self._calculate_mid_point_from_output_nodes(
                source_node, output_nodes_in_front, data, i, settings
            )
            data.base_dot_node[i].set_position(
                data.base_dot_node[i].pos.x, mid_point
            )

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
