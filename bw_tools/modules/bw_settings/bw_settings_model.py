from PySide2 import QtGui
from PySide2 import QtCore


class ModuleModel(QtGui.QStandardItemModel):
    def __init__(self, parent=None):
        super(ModuleModel, self).__init__(parent)

    def data(self, index, role):
        return QtGui.QStandardItemModel.data(self, index, role)
