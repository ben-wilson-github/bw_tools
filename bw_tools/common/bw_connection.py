class InputConnection(object):
    def __init__(self, connected_node):
        if not isinstance(connected_node, int):
            raise TypeError('Unable to create InputConnection. Supported types are : int')

        self._connected_node = connected_node

    @property
    def connected_node(self):
        return self._connected_node


class OutputConnection(object):
    def __init__(self, connected_nodes):
        msg = 'Unable to create OutputConnection. Supported types are : [int], (int)'
        if not isinstance(connected_nodes, (list, tuple)):
            raise TypeError(msg)
        elif len(connected_nodes) < 1:
            raise TypeError('Unable to create OutputConnection. Can not initialize with empty data')

        if any(not isinstance(x, int) for x in connected_nodes):
            raise TypeError(msg)

        self._connected_nodes = tuple(connected_nodes)

    @property
    def connected_nodes(self):
        return self._connected_nodes

    def connected_node(self, index):
        try:
            id = self.connected_nodes[index]
        except IndexError:
            raise IndexError('Unable to get connected node. Index is out of range')
        else:
            return id
