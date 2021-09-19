from PySide2 import QtGui


class ModuleModel(QtGui.QStandardItemModel):
    def __init__(self, parent=None):
        super(ModuleModel, self).__init__(parent)
