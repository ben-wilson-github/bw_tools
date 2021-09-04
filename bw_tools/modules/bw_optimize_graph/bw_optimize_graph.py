from __future__ import annotations
from bw_tools.common.bw_node_selection import NodeSelection
from bw_tools.common.bw_api_tool import SDNode

from typing import TYPE_CHECKING
from typing import List
from pathlib import Path
from functools import partial

import json, os, time
import importlib.util

from . import optimize_uniform_color_nodes

if TYPE_CHECKING:
    from bw_tools.common.bw_api_tool import APITool

from sd.api.sdproperty import SDPropertyCategory, SDPropertyInheritanceMethod
from sd.api.apiexception import APIException
from sd.api.sdvalueint2 import SDValueInt2
from sd.api.sdvalueenum import SDValueEnum
from sd.api.sdtypeenum import SDTypeEnum
from sd.api.sdbasetypes import int2
from sd.api.sdhistoryutils import SDHistoryUtils

from PySide2 import QtGui, QtWidgets


class OptimizeGraph(object):
    def __init__(self, aUIMgr, aLogger, aVerbose=False):
        self._uiMgr = aUIMgr
        self._logger = aLogger
        self._verbose = aVerbose

    @property
    def verbose(self):
        return self._verbose
    
    @property
    def uiMgr(self):
        return self._uiMgr

    @property
    def logger(self):
        return self._logger

    def _propertiesMatch(self, aNode, aUniqueNode):
        """
        Returns true if the properties match, otherwise false.
        """
        # Check each input property
        for uniqueNodeProperty in aUniqueNode.getProperties(SDPropertyCategory.Input):
            # Try to get the same property from the node
            try:
                nodeProperty = aNode.getPropertyFromId(uniqueNodeProperty.getId(), SDPropertyCategory.Input)
            except AttributeError:
                return False
            else:
                if not nodeProperty:
                    return False
                # The properties are the same, but the values might not be
                # Check there is no function graph on either the property
                if aNode.getPropertyGraph(nodeProperty):
                    return False
                elif aUniqueNode.getPropertyGraph(uniqueNodeProperty):
                    return False

                # If the property is connectable, check the input nodes are the same
                if nodeProperty.isConnectable():
                    # Get the connection for the property
                    nodeConnection = aNode.getPropertyConnections(nodeProperty)
                    uniqueNodeConnection = aUniqueNode.getPropertyConnections(uniqueNodeProperty)
                    # If the len of connections are different, they do not match
                    if len(nodeConnection) != len(uniqueNodeConnection):
                        return False
                    
                    # Try to get the connected nodes
                    for i in range(len(nodeConnection)):
                        connectedNodeOfNode = nodeConnection[i].getInputPropertyNode()
                        connectNodeOfUniqueNode = uniqueNodeConnection[i].getInputPropertyNode()

                        if connectedNodeOfNode.getIdentifier() != connectNodeOfUniqueNode.getIdentifier():
                            return False

                # Then make sure the values match
                try:
                    nodeValue = aNode.getInputPropertyValueFromId(uniqueNodeProperty.getId()).get()
                    uniqueNodeValue = aUniqueNode.getInputPropertyValueFromId(uniqueNodeProperty.getId()).get()
                except OSError as e:
                    return False
                except AttributeError:
                    continue
                else:
                    if str(nodeValue) != str(uniqueNodeValue):
                        return False

        # All the properties match, so these two nodes are the same
        return True

    def _isDuplicate(self, aNode, aUniqueNode):
        """
        Returns the true is aNode is a duplciate of aUniqueNode, otherwise will return False
        """
        # If the labels do not match, they are not the same
        if aNode.getDefinition().getLabel() != aUniqueNode.getDefinition().getLabel():
            return False
        
        # If the properties do not match, they are not the same
        if not self._propertiesMatch(aNode, aUniqueNode):
            return False
        else:
            return True

    def _hasInputs(self, aNode):
        # Check if the node has inputs
        for inputProperty in aNode.getProperties(SDPropertyCategory.Input):
            if inputProperty.isConnectable():
                return True
        return False

    def _parseNodes(self, aNodeList):
        """
        Given a list of nodes, will generate a list of unique nodes and any duplicates
        """
        uniformColorNodes = []
        inputBasedCompNodes = []
        compNodes = []
        blendNodes = []

        for node in aNodeList:
            nodeID = node.getDefinition().getId()

            # Handle Blend nodes
            if nodeID == 'sbs::compositing::blend':
                blendNodes.append(node)
            # Handle Uniform Color nodes
            elif nodeID == 'sbs::compositing::uniform':
                uniformColorNodes.append(node)
            # Handle comp graph nodes
            elif nodeID == 'sbs::compositing::sbscompgraph_instance':
                if not node.getReferencedResource():
                    continue
                if self._hasInputs(node):
                    inputBasedCompNodes.append(node)
                else:
                    compNodes.append(node)
                
        return inputBasedCompNodes, compNodes, uniformColorNodes, blendNodes
    
    def _getPixelFormatFromConnection(self, aGraph, aBlendNode, aConnection):
        """
        Returns the pixel format given a connection.
        """
        inputNode = aConnection.getInputPropertyNode()
        inputProperty = aConnection.getInputProperty()
        outputProperty = aConnection.getOutputProperty()
        
        # Get the value
        try:
            pixelFormat = inputNode.getPropertyValue(inputProperty).get().getPixelFormat()
        except AttributeError:  # Fails when the graph is not computed
            # Add a tmp output and compute the graph
            tmpOutput = aGraph.newNode('sbs::compositing::output')
            aBlendNode.newPropertyConnectionFromId('unique_filter_output', tmpOutput, 'inputNodeOutput')
            aGraph.compute()
            pixelFormat = inputNode.getPropertyValue(inputProperty).get().getPixelFormat()
            aGraph.deleteNode(tmpOutput)
        finally:
            return str(pixelFormat)
    
    def deleteNodeAndReconnect(self, aGraph, aUniqueNode, aDuplicateNode):
        """
        Reconnect and delete any duplicate nodes.
        """
        # Loop through each output property for the duplicate node
        duplicateNodeProperties = aDuplicateNode.getProperties(SDPropertyCategory.Output)
        for duplicateNodeProperty in duplicateNodeProperties:
                # Loop through each connection for the given output property
                connections = aDuplicateNode.getPropertyConnections(duplicateNodeProperty)
                for connection in connections:
                    connectedNode = connection.getInputPropertyNode()
                    connectedNodeProperty = connection.getInputProperty()
                    uniqueNodeProperty = aUniqueNode.getPropertyFromId(duplicateNodeProperty.getId(), SDPropertyCategory.Output)

                    # create new connection between the unique node and the connected node
                    aUniqueNode.newPropertyConnection(uniqueNodeProperty, connectedNode, connectedNodeProperty)
                
        #  Then delete the duplicate node
        aGraph.deleteNode(aDuplicateNode)

    def optimizeUniformColor(self, aUniformColorNode):
        """
        Forces a uniform color node to 16x16 and sets any connected nodes to relativeToParent if
        they were not manually modified
        """
        # force 16x16
        outputSizeProperty = aUniformColorNode.getPropertyFromId('$outputsize', SDPropertyCategory.Input)
        aUniformColorNode.setPropertyInheritanceMethod(outputSizeProperty, SDPropertyInheritanceMethod.Absolute)
        aUniformColorNode.setPropertyValue(outputSizeProperty, SDValueInt2.sNew(int2(4,4)))

        # Handle connected nodes
        outputProperty = aUniformColorNode.getPropertyFromId('unique_filter_output', SDPropertyCategory.Output)
        connections = aUniformColorNode.getPropertyConnections(outputProperty)
        for connection in connections:
            # If we are able to get the connected node properties, then ignore it. Likely connected to an output node
            try:
                connectedNode = connection.getInputPropertyNode()
                connectedNodeOutputSizeProperty = connectedNode.getPropertyFromId('$outputsize', SDPropertyCategory.Input)
                connectedNodeInheritanceMethod = connectedNode.getPropertyInheritanceMethod(connectedNodeOutputSizeProperty)
            except AttributeError:
                continue
            else:
                # If relative to input, force to relative to parent
                if connectedNodeInheritanceMethod == SDPropertyInheritanceMethod.RelativeToInput:
                    connectedNode.setPropertyInheritanceMethod(connectedNodeOutputSizeProperty, SDPropertyInheritanceMethod.RelativeToParent)

    def optimizeBlendNode(self, aGraph, aBlendNode):
        """
        Optimizes a blend node. Will turn off alpha blending if both inputs are grayscale
        """
        bgID = 'destination'
        fgID = 'source'

        # get the blending mode and skip if already set to ignore value
        blendingMode = aBlendNode.getPropertyValueFromId('colorblending', SDPropertyCategory.Input).get()
        if blendingMode == 1:
            return False
        
        # Check input slots
        try:
            bgProperty = aBlendNode.getPropertyFromId(bgID, SDPropertyCategory.Input)
            bgConnections = aBlendNode.getPropertyConnections(bgProperty)

            fgProperty = aBlendNode.getPropertyFromId(fgID, SDPropertyCategory.Input)
            fgConnections = aBlendNode.getPropertyConnections(fgProperty)
        except AttributeError:
            return False

        # If there are missing connections, return
        if not bgConnections or not fgConnections:
            return False  
        else:
            bgConnection = bgConnections[0]
            fgConnection = fgConnections[0]
        
        
        bgPixelFormat = self._getPixelFormatFromConnection(aGraph, aBlendNode, bgConnection)
        fgPixelFormat = self._getPixelFormatFromConnection(aGraph, aBlendNode, fgConnection)

        grayscaleFormat = ['SBSPixelFormat.LUM16', 'SBSPixelFormat.LUM16F', 'SBSPixelFormat.LUM32F', 'SBSPixelFormat.LUM8']

        if bgPixelFormat in grayscaleFormat or fgPixelFormat in grayscaleFormat:
            aBlendNode.setInputPropertyValueFromId('colorblending', SDValueEnum.sFromValueId('sbs::compositing::colorblending', 'ignorealpha'))
            return True
        else:
            return False

    def prepareGraph(self, aGraph):
        """
        Forces the graph to 16x16 and disconnects the output nodes.
        This is to speed up the optimising process
        """
        if self.verbose:
            self.logger.info(f'{"."*5}Preparing graph...')
        # force graph to 16x16 and disconnect the output nodes
        graphOutputSizeProperty = aGraph.getPropertyFromId('$outputsize', SDPropertyCategory.Input)
        graphOutputSize = aGraph.getPropertyValue(graphOutputSizeProperty)
        graphOutputMode = aGraph.getPropertyInheritanceMethod(graphOutputSizeProperty)

        aGraph.setPropertyInheritanceMethod(graphOutputSizeProperty, SDPropertyInheritanceMethod.Absolute)
        aGraph.setPropertyValue(graphOutputSizeProperty, SDValueInt2.sNew(int2(4,4)))

        # detach outputs
        outputNodeDict = {}
        outputNodes = aGraph.getOutputNodes()
        if self.verbose:
            self.logger.info(f'{"."*10}Found output nodes:')
        for outputNode in outputNodes:
            if self.verbose:
                self.logger.info(f'{"."*10}{outputNode.getDefinition().getLabel()}')
            
            connectionDict = {}

            try:
                connection = outputNode.getPropertyConnections(outputNode.getPropertyFromId('inputNodeOutput', SDPropertyCategory.Input))[0]
            except:
                if self.verbose:
                    self.logger.info(f'{"."*15}Output {outputNode.getAnnotationPropertyValueFromId("identifier").get()} is not connected to anything, ignoring')
                continue
            else:
                connectionDict['inputNode'] = connection.getInputPropertyNode()
                connectionDict['inputProperty'] = connection.getInputProperty()
                connectionDict['outputProperty'] = connection.getOutputProperty()

                outputNodeDict[outputNode] = connectionDict

            outputNode.deletePropertyConnections(connection.getOutputProperty())
        
        return outputNodeDict, graphOutputMode, graphOutputSize
    
    def restoreGraph(self, aGraph, aOutputNodeDict, aGraphOutputMode, aGraphOutputSize):
        """
        Restores the graph to how it was before the optimising process
        """
        # restore output nodes
        for outputNode, outputNodeConnection in aOutputNodeDict.items():
            inputNode = outputNodeConnection['inputNode']
            inputNodeProperty = outputNodeConnection['inputProperty']

            inputNode.newPropertyConnection(inputNodeProperty, outputNode, outputNodeConnection['outputProperty'])

        # restore graph size
        graphOutputSizeProperty = aGraph.getPropertyFromId('$outputsize', SDPropertyCategory.Input)
        aGraph.setPropertyInheritanceMethod(graphOutputSizeProperty, aGraphOutputMode)
        aGraph.setPropertyValue(graphOutputSizeProperty, aGraphOutputSize)

    def deleteDuplicateNodes(self, aGraph, aNodeList, aDeleteCount):
        """
        Given a list of nodes, will delete any duplicates found inside.
        """
        uniqueNodes = []
        isDup = False
        runAgain = False

        for node in aNodeList:
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

def run(node_selection: NodeSelection):
    if node_selection.node_count == 0:
        return

        
    total_delete_count = 0
    total_uniform_nodes = 0
    total_blend_nodes = 0

    
    
    # # intialise
    # og = OptimizeGraph(aUIMgr, aLogger, verbose)


    # Parse the nodes
    # inputBasedCompNodes, compNodes, uniformColorNodes, blendNodes = og._parseNodes(selectedNodes)
    

    # Handle uniform colors
    optimizer = optimize_uniform_color_nodes.UniformOptimizer(node_selection)
    optimizer.run()
    # if verbose:
    #     if moduleSettings['uniformColorNodes']['outputSize'] or moduleSettings['uniformColorNodes']['removeDuplicates']:
    #         og.logger.info(f'{"."*5}Optimizing color nodes...')
            
    
    if moduleSettings['uniformColorNodes']['removeDuplicates']:
        uniformColorNodes, _, deleteCount = og.deleteDuplicateNodes(currentGraph, uniformColorNodes, 0)
        total_delete_count += deleteCount
        if verbose:
            og.logger.info(f'{"."*10}Looking for duplicate nodes...')
            og.logger.info(f'{"."*15}Deleted {deleteCount} duplicate nodes')
    
    if moduleSettings['uniformColorNodes']['outputSize']:
        for node in uniformColorNodes:
            og.optimizeUniformColor(node)
        if verbose:
            og.logger.info(f'{"."*10}Setting Uniform Color nodes output size...')
            og.logger.info(f'{"."*15}Optimized {len(uniformColorNodes)} nodes')
        total_uniform_nodes += len(uniformColorNodes)
    
    # Handle Blend Nodes
    if moduleSettings['blendNodes']['ignoreAlpha']:
        successCounter = 0
        for blendNode in blendNodes:
            if og.optimizeBlendNode(currentGraph, blendNode):
                successCounter += 1
        if verbose:
            og.logger.info(f'{"."*5}Optimizing Blend Nodes...')
            og.logger.info(f'{"."*10}Optimized {successCounter} nodes')
        total_blend_nodes += successCounter

    # Handle compNodes
    if moduleSettings['compositeNodes']['removeDuplicates']:  
        _, _, deleteCount = og.deleteDuplicateNodes(currentGraph, compNodes, 0)
        if verbose:
            og.logger.info(f'{"."*5}Optimising comp nodes...')
            og.logger.info(f'{"."*10}Deleted {deleteCount} duplicate nodes')

        # Handle input based compNodes
        if moduleSettings['compositeNodes']['evaluateInputChain']:
            uniqueNodes, runAgain, deleteCount = og.deleteDuplicateNodes(currentGraph, inputBasedCompNodes, deleteCount)
            while runAgain:
                uniqueNodes, runAgain, deleteCount = og.deleteDuplicateNodes(currentGraph, uniqueNodes, deleteCount)
            if verbose:
                og.logger.info(f'{"."*5}Evaluating input chains...')
                og.logger.info(f'{"."*10}Deleted {deleteCount} duplicate nodes')
    
    total_delete_count += deleteCount
    
    # restore the graph
    if moduleSettings['blendNodes']['ignoreAlpha']:
        og.restoreGraph(currentGraph, outputNodeDict, graphOutputMode, graphOutputSize)

    end = time.time()
    elapsedTime = end - start
    aLogger.info(f'{"."*5}{total_delete_count} duplicate nodes deleted')
    aLogger.info(f'{"."*5}{total_blend_nodes} blend nodes optimized')
    aLogger.info(f'{"."*5}{total_uniform_nodes} uniform color nodes optimized')

    if moduleSettings['popupOnCompletion']:
        txt = f'{total_delete_count} duplicate nodes deleted\n{total_blend_nodes} blend nodes optimized\n{total_uniform_nodes} uniform color nodes optimized'
        QtWidgets.QMessageBox.information(
            None,
            '',
            txt,
            QtWidgets.QMessageBox.Ok)

    aLogger.info(f'Optimize graph ran in {elapsedTime} seconds')

def _on_clicked_run(api: APITool):
    with SDHistoryUtils.UndoGroup('Optimize Nodes'):
        api.log.info('Running optimize graph...')
        node_selection = NodeSelection(api.current_selection, api.current_graph)
        run(node_selection)

def on_graph_view_created(_, api: APITool):
    # settings = StraightenSettings(
    #     Path(__file__).parent / "bw_straighten_connection_settings.json"
    # )

    icon = Path(__file__)
    action = api.graph_view_toolbar.addAction("O")
    # action.setShortcut(QtGui.QKeySequence(settings.target_hotkey))
    action.setToolTip("Optimize graph")
    action.triggered.connect(lambda: _on_clicked_run(api))

def on_initialize(api: APITool):
    api.register_on_graph_view_created_callback(
        partial(on_graph_view_created, api=api)
    )
    

def writeDefaultSettings(aSettingsFilePath):
    bwOptimizeGraphSettings = {}
    bwOptimizeGraphSettings['hotkey'] = 'Ctrl+Alt+C'
    bwOptimizeGraphSettings['popupOnCompletion'] = True
    bwOptimizeGraphSettings['detailedLog'] = False

    uniformColorNodes = {}
    uniformColorNodes['removeDuplicates'] = True
    uniformColorNodes['outputSize'] = 16
    bwOptimizeGraphSettings['uniformColorNodes'] = uniformColorNodes 

    blendNodes = {}
    blendNodes['ignoreAlpha'] = False
    bwOptimizeGraphSettings['blendNodes'] = blendNodes

    compositeNodes = {}
    compositeNodes['removeDuplicates'] = True
    compositeNodes['evaluateInputChain'] = True
    bwOptimizeGraphSettings['compositeNodes'] = compositeNodes

    with open(aSettingsFilePath) as settingsFile:
        data = json.load(settingsFile)
        data['module'][bwSettings.SupportedModules.OptimizeGraph.value] = bwOptimizeGraphSettings

    with open(aSettingsFilePath, 'w') as settingsFile:
        json.dump(data, settingsFile, indent=4)
    