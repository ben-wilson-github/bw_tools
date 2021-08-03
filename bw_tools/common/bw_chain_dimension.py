from __future__ import annotations
from dataclasses import dataclass
from dataclasses import field
from typing import Union, List

from bw_tools.common import bw_node, bw_node_selection


class OutOfBoundsError(ValueError):
    def __init__(self):
        super().__init__('Node not in bounds.')

class NotInChainError(AttributeError):
    def __init__(self):
        super().__init__('Node is not in chain.')


@dataclass()
class Bound:
     left: Union[float, None] = None
     right: Union[float, None] = None
     upper: Union[float, None] = None
     lower: Union[float, None] = None


@dataclass()
class ChainDimension:
    bounds: Bound = field(init=False, default_factory=Bound)
    left_node: bw_node.Node = field(init=False, default=None)
    right_node: bw_node.Node = field(init=False, default=None)
    upper_node: bw_node.Node = field(init=False, default=None)
    lower_node: bw_node.Node = field(init=False, default=None)

    @property
    def width(self):
        return self.bounds.right - self.bounds.left


def node_in_bounds(node: bw_node.Node, bounds: Bound):
    # Setup testing bounds
    testing_bounds = Bound(
        left=bounds.left,
        right=bounds.right,
        upper=bounds.upper,
        lower=bounds.lower,
    )
    # So we can resolve any undefined bounds
    # Setting bounds to node position will ensure it passes
    # a bounds check
    if testing_bounds.left is None:
        testing_bounds.left = node.pos.x
    if testing_bounds.right is None:
        testing_bounds.right = node.pos.x
    if testing_bounds.upper is None:
        testing_bounds.upper = node.pos.y
    if testing_bounds.lower is None:
        testing_bounds.lower = node.pos.y

    if (node.pos.x >= testing_bounds.left
            and node.pos.x <= testing_bounds.right
            and node.pos.y >= testing_bounds.upper
            and node.pos.y <= testing_bounds.lower):
        return True
    else:
        return False


def calculate_chain_dimension(node: bw_node.Node,
                              chain: List[bw_node.Node],
                              limit_bounds: Bound = Bound
                              ) -> ChainDimension:

    if node not in chain:
        raise NotInChainError()
    if not node_in_bounds(node, limit_bounds):
        raise OutOfBoundsError()

    cd = ChainDimension()
    cd.bounds = Bound(
        right=node.pos.x + (node.width / 2),
        left=node.pos.x - (node.width / 2),
        lower=node.pos.y + (node.height / 2),
        upper=node.pos.y - (node.height / 2)
    )

    cd.left_node = node
    cd.right_node = node
    cd.upper_node = node
    cd.lower_node = node

    for input_node in node.input_nodes:
        if input_node not in chain:
            continue
        else:
            if node_in_bounds(input_node, limit_bounds):
                input_cd = calculate_chain_dimension(input_node,
                                                     chain,
                                                     limit_bounds=limit_bounds)

                if input_cd.bounds.left <= cd.bounds.left:
                    cd.bounds.left = input_cd.bounds.left
                    cd.left_node = input_cd.left_node

                # designer coords are flipped in y
                if input_cd.bounds.upper <= cd.bounds.upper:
                    cd.bounds.upper = input_cd.bounds.upper
                    cd.upper_node = input_cd.upper_node
                if input_cd.bounds.lower >= cd.bounds.lower:
                    cd.bounds.lower = input_cd.bounds.lower
                    cd.lower_node = input_cd.lower_node

    return cd
