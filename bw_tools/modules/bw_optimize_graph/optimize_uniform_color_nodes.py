from __future__ import annotations, unicode_literals
from enum import unique
from bw_tools.common.bw_api_tool import NodeID, SDSBSCompGraph
from typing import List, TYPE_CHECKING, Tuple
from sd.api.sdproperty import SDPropertyCategory, SDPropertyInheritanceMethod
from . import property_matcher

if TYPE_CHECKING:
    from bw_tools.common.bw_node import Node
    from bw_tools.common.bw_node_selection import NodeSelection


def run(node_selection: NodeSelection):
    uniform_color_nodes = _get_uniform_color_nodes(node_selection)
    unique_nodes, duplicate_nodes = _sort_nodes(uniform_color_nodes)
    print(duplicate_nodes)


def _get_uniform_color_nodes(node_selection: NodeSelection) -> List[Node]:
    return [
        node
        for node in node_selection.nodes
        if node.api_node.getDefinition().getId() == NodeID.UNIFORM_COLOR.value
    ]


def _sort_nodes(nodes: List[Node]) -> Tuple[Tuple[Node], Tuple[Node]]:
    unique_nodes: List[Node] = list()
    duplicate_nodes: List[Node] = list()
    for node in nodes:
        if _is_duplicate(node, unique_nodes):
            duplicate_nodes.append(node)
        else:
            unique_nodes.append(node)
    return tuple(unique_nodes), tuple(duplicate_nodes)


def _is_duplicate(node: Node, unique_nodes: List[Node]):
    return any(
        property_matcher.input_properties_match(node, unique_node)
        for unique_node in unique_nodes
    )


def delete_duplicate_nodes(self, graph: SDSBSCompGraph, node_list: List[Node]):
    """
    Given a list of nodes, will delete any duplicates found inside.
    """
    uniqueNodes = []
    isDup = False
    runAgain = False

    for node in node_list:
        # compare each node against a running list of unique nodes
        for i, uniqueNode in enumerate(uniqueNodes):
            if not self._isDuplicate(node, uniqueNode):
                # It is not a duplicate, continue to check the rest
                isDup = False
                continue
            else:
                # It is a duplicate, so delete it
                self.deleteNodeAndReconnect(aGraph, uniqueNode, node)
                aDeleteCount += 1
                isDup = True
                runAgain = True
                break

        if not isDup:
            uniqueNodes.append(node)

    return uniqueNodes, runAgain, aDeleteCount
