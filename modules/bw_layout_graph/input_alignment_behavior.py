from abc import ABC
from abc import abstractmethod
from dataclasses import Field, dataclass, field, fields

from typing import Tuple

from common import bw_node
from common import bw_node_selection
from common import bw_chain_dimension

from . import utils
from . import post_alignment_behavior as pab


SPACER = 32


@dataclass
class NodeAlignmentBehavior(ABC):
    @abstractmethod
    def exec(self):
        pass


@dataclass
class StaticAlignment(NodeAlignmentBehavior):
    offset: bw_node.Float2() = field(default_factory=bw_node.Float2)

    def exec(self):
        pass


@dataclass
class AverageToOutputs(NodeAlignmentBehavior):
    def exec(self):
        pass





def align_in_line(input_node: bw_node.Node, target_node: bw_node.Node):
    input_node.set_position(input_node.pos.x, target_node.pos.y)


def align_below(node: bw_node.Node, target_node: bw_node.Node):
    y = target_node.pos.y + (target_node.height / 2) + SPACER + (node.height / 2)
    node.set_position(node.pos.x, y)


def align_above(node: bw_node.Node, target_node: bw_node.Node):
    y = target_node.pos.y - (target_node.height / 2) - SPACER - (node.height / 2)
    node.set_position(node.pos.x, y)


def align_above_bound(node: bw_node.Node, lower_bound: float, upper_bound: float):
    offset = upper_bound - lower_bound
    node.set_position(node.pos.x, node.pos.y + offset)


def align_below_bound(node: bw_node.Node, lower_bound: float, upper_bound: float):
    offset = lower_bound - upper_bound
    node.set_position(node.pos.x, node.pos.y + offset)


def align_node_between(node: bw_node.Node, top: bw_node.Node, bottom: bw_node.Node):
    _, mid_point = utils.calculate_mid_point(top, bottom)
    node.set_position(node.pos.x, mid_point)