from PySide2.QtWidgets import QToolBar


class BWToolbar(QToolBar):
    def __init__(self, parent):
        super().__init__(parent=parent)
        self.uid = self.__class__.__name__
        self.objectName = self.uid
