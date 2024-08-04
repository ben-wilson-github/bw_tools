from PySide6.QtWidgets import QToolBar
from PySide6.QtGui import QAction


class BWToolbar(QToolBar):
    def __init__(self, parent):
        super().__init__(parent=parent)
        self.uid = self.__class__.__name__
        self.objectName = self.uid
        self._actions = dict()

    def add_action(self, id: str, action: QAction):
        if id in self._actions:
            return
        self.addAction(action)
        self._actions[id] = action
