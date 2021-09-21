from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, List, Union

if TYPE_CHECKING:
    from bw_tools.common.bw_node import BWNode


class BWOutOfBoundsError(ValueError):
    def __init__(self):
        super().__init__("Node not in bounds.")


class BWNotInChainError(AttributeError):
    def __init__(self):
        super().__init__("Node is not in chain.")


@dataclass()
class BWBound:
    left: Union[float, None] = None
    right: Union[float, None] = None
    upper: Union[float, None] = None
    lower: Union[float, None] = None


@dataclass()
class BWChainDimension:
    bounds: BWBound = field(init=False, default_factory=BWBound, repr=False)
    left_node: BWNode = field(init=False, default=None)
    right_node: BWNode = field(init=False, default=None)
    upper_node: BWNode = field(init=False, default=None, repr=False)
    lower_node: BWNode = field(init=False, default=None, repr=False)
    node_count: int = 0

    @property
    def width(self):
        return self.bounds.right - self.bounds.left


def node_in_bounds(node: BWNode, bounds: BWBound):
    # Setup testing bounds
    testing_bounds = BWBound(
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

    if (
        node.pos.x >= testing_bounds.left
        and node.pos.x <= testing_bounds.right
        and node.pos.y >= testing_bounds.upper
        and node.pos.y <= testing_bounds.lower
    ):
        return True
    else:
        return False


def calculate_chain_dimension(
    node: BWNode,
    selection: List[BWNode],
    limit_bounds: BWBound = BWBound,
) -> BWChainDimension:
    """
    Caluclates the bounds of the input chain of a node, given a list of nodes
    in a selection.

    The bounds are calculated by recursively running down the inputs of the
    node. Any input nodes which are not in the selection are ignored.
    If the given node is not in the selection, raise NotInChainError.

    Optionally, a checking bound can be supplied to further limit the
    calculation. If an input not is not within the bound, raise
    OutOfBoundsError.

    Selectively controlling which nodes you pass into selection, means you can
    dynamically adjust and define bound calculations. For example, you may wish
    to exclude branching input nodes or simply supply the entire node chain.
    """

    if node not in selection:
        raise BWNotInChainError()
    if not node_in_bounds(node, limit_bounds):
        raise BWOutOfBoundsError()

    cd = BWChainDimension()
    cd.bounds = BWBound(
        right=node.pos.x + (node.width / 2),
        left=node.pos.x - (node.width / 2),
        lower=node.pos.y + (node.height / 2),
        upper=node.pos.y - (node.height / 2),
    )

    cd.left_node = node
    cd.right_node = node
    cd.upper_node = node
    cd.lower_node = node

    cd.node_count = 1

    for input_node in node.input_nodes:
        if input_node not in selection:
            continue
        else:
            if node_in_bounds(input_node, limit_bounds):
                input_cd = calculate_chain_dimension(
                    input_node, selection, limit_bounds=limit_bounds
                )

                cd.node_count += input_cd.node_count

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
