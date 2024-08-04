from PySide6.QtGui import QStandardItemModel


class BWModuleModel(QStandardItemModel):
    def __init__(self, parent=None):
        super(BWModuleModel, self).__init__(parent)
