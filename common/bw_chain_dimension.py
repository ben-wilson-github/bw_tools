from dataclasses import dataclass


@dataclass()
class ChainDimension:
    min_x: float
    max_x: float
    min_y: float
    max_y: float

    @property
    def width(self):
        return self.max_x - self.min_x


class OldChainDimension(object):
    def __init__(
            self,
            aSourceNode,
            aTerminateOnSplitNodes=False,
            aLimitByDistance=False,
            aTerminatorNodeList=[],
            aXPositionTerminator=False,
            aTerminateOnNonYParents=False
    ):
        self._sourceNode = aSourceNode
        self._endNode = aSourceNode
        self._nodes = {}
        self._terminatorNodes = aTerminatorNodeList
        self._xPositionTerminator = aXPositionTerminator
        self._limit = aLimitByDistance
        self._terminateOnSplitNodes = aTerminateOnSplitNodes
        self._terminateOnNonYParents = aTerminateOnNonYParents
        # self._nodeCount = 0
        self._largestStepCount = 0
        self._shortestStepCount = None
        self._minX = aSourceNode.positionX - (aSourceNode.width / 2)
        self._maxX = aSourceNode.positionX + (aSourceNode.width / 2)
        self._minY = aSourceNode.positionY - (aSourceNode.height / 2)
        self._maxY = aSourceNode.positionY + (aSourceNode.height / 2)

        self._parseNodes()
        self._findShortestStepsToEnd()

    @property
    def sourceNode(self):
        return self._sourceNode

    @property
    def endNode(self):
        return self._endNode

    @endNode.setter
    def endNode(self, aNode):
        self._endNode = aNode

    @property
    def nodes(self):
        return list(self._nodes.values())

    @property
    def limit(self):
        return self._limit

    @property
    def terminateOnSplitNodes(self):
        return self._terminateOnSplitNodes

    @property
    def xPositionTerminator(self):
        return self._xPositionTerminator

    @property
    def terminateOnNonYParents(self):
        return self._terminateOnNonYParents

    @property
    def minX(self):
        return self._minX

    @minX.setter
    def minX(self, aValue):
        self._minX = aValue

    @property
    def maxX(self):
        return self._maxX

    @maxX.setter
    def maxX(self, aValue):
        self._maxX = aValue

    @property
    def minY(self):
        return self._minY

    @minY.setter
    def minY(self, aValue):
        self._minY = aValue

    @property
    def maxY(self):
        return self._maxY

    @maxY.setter
    def maxY(self, aValue):
        self._maxY = aValue

    @property
    def width(self):
        return self.maxX - self.minX

    @property
    def height(self):
        return self.maxY - self.minY

    @property
    def nodeCount(self):
        return len(self.nodes)
        # return self._nodeCount

    @nodeCount.setter
    def nodeCount(self, aValue):
        self._nodeCount = aValue

    @property
    def largestStepCount(self):
        return self._largestStepCount

    @largestStepCount.setter
    def largestStepCount(self, aValue):
        self._largestStepCount = aValue

    @property
    def shortestStepCount(self):
        return self._shortestStepCount

    @shortestStepCount.setter
    def shortestStepCount(self, aValue):
        self._shortestStepCount = aValue

    @property
    def terminatorNodes(self):
        return self._terminatorNodes

    def _findDeepestNode(self, aNode, aIgnoreNode):
        def _checkChildren(aNode, aIgnoreNode, aParentNode):
            if aNode is aIgnoreNode:
                return aParentNode

            if aNode.isEnd:
                return aNode

            deepestNode = aNode
            for child in aNode.children:
                if child.positionX >= (aNode.positionX - child.getOffsetForSingleStep(aNode)):
                    retNode = _checkChildren(child, aIgnoreNode, aNode)
                    if retNode.positionX < deepestNode.positionX:
                        deepestNode = retNode
                else:
                    continue

            return deepestNode

        endChild = _checkChildren(aNode, aIgnoreNode, None)
        return endChild

    def _parseNodes(self):
        def _parseNext(aNode, aParentNode, aStep):

            verbose = False

            if verbose:
                print(f'...Parsing {aNode.label}')

            if self.limit:
                if verbose:
                    print(f'......Chain Dimension is checking for limits')
                # If the node is too far away, return
                # A node will be considered too far away if it is further than the deepest node in
                # all the other branches of the parent
                if aParentNode:
                    deepestNode = self._findDeepestNode(aParentNode, aNode)
                    if verbose:
                        print(f'..........Deepest Node : {deepestNode.label}')
                    if aNode.positionX < (deepestNode.positionX - aNode.getOffsetForSingleStep(aParentNode)):
                        return

            if aNode in self.terminatorNodes:
                if verbose:
                    print(f'......Node is in the termination list')
                return

            if self.terminateOnSplitNodes:
                if aParentNode:
                    if aNode.isSplit:
                        if aNode.positionX != aParentNode.positionX:
                            if verbose:
                                print(f'.....Node is a split Node, returning')
                        return

            if self.xPositionTerminator is not False:
                if aNode.positionX <= self.xPositionTerminator:
                    if verbose:
                        print(f'.....Node is past the x terminator, returning')
                    return

            if self.terminateOnNonYParents:
                if verbose:
                    print(f'TerminateOnNonYParents is on')
                if aParentNode:
                    # if aNode.yParent is not aParentNode:
                    if aNode.furthestParentInX is not aParentNode:
                        if verbose:
                            print(f'.....Nodes yParent is not the currently processing parent node, returning')
                        return

            if verbose:
                print(f'......Updating chain metrics')
            # update the chain metrics
            self._nodes[aNode.identifier] = aNode
            # self.nodeCount += 1
            if aStep > self.largestStepCount:
                self.largestStepCount = aStep

            if aNode.positionX - (aNode.width / 2) < self.minX:
                self.minX = aNode.positionX - (aNode.width / 2)
                self.endNode = aNode

            self.minY = min(self.minY, aNode.positionY - (aNode.height / 2))
            self.maxY = max(self.maxY, aNode.positionY + (aNode.height / 2))

            # End of chain state
            if not aNode.children:
                if verbose:
                    print(f'......Node has no children, end of chain')
                return

            for childNode in aNode.children:
                if verbose:
                    print(f'......Parsing next. {childNode.label}')
                _parseNext(childNode, aNode, aStep + 1)

        return _parseNext(self.sourceNode, self.sourceNode.yParent, 1)

    def _findShortestStepsToEnd(self):
        def _checkChildren(aNode, aStep):
            if aNode in self.terminatorNodes:
                return

            elif aNode is self.endNode:
                if self.shortestStepCount is None:
                    self.shortestStepCount = aStep
                elif aStep < self.shortestStepCount:
                    self.shortestStepCount = aStep
                return

            else:
                for childNode in aNode.children:
                    _checkChildren(childNode, aStep + 1)

        _checkChildren(self.sourceNode, 1)

    def __str__(self):
        retString = f'{type(self)}'
        retString += f'\n{"." * 5}Chain Node Count    : {self.nodeCount}'
        retString += f'\n{"." * 5}Largest Step Count  : {self.largestStepCount}'
        retString += f'\n{"." * 5}Shortest Step Count : {self.shortestStepCount}'
        retString += f'\n{"." * 5}Source              : {self.sourceNode.label}'
        retString += f'\n{"." * 5}End                 : {self.endNode.label}'
        retString += f'\n{"." * 5}Width               : {self.width}'
        retString += f'\n{"." * 5}Height              : {self.height}'
        retString += f'\n{"." * 5}Min X               : {self.minX}'
        retString += f'\n{"." * 5}Max X               : {self.maxX}'
        retString += f'\n{"." * 5}Min Y               : {self.minY}'
        retString += f'\n{"." * 5}Max Y               : {self.maxY}'

        return retString
