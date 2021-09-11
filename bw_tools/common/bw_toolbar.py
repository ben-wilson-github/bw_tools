from PySide2 import QtWidgets


class BWToolbar(QtWidgets.QToolBar):
    def __init__(self, parent):
        super().__init__(parent=parent)
        self.uid = self.__class__.__name__
