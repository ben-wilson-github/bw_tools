from PySide2 import QtWidgets


class StringValueWidget(QtWidgets.QWidget):
    def __init__(self, label: str, parent=None):
        super().__init__(parent=parent)

        self.setLayout(QtWidgets.QGridLayout())

        label_widget = QtWidgets.QLabel(label)
        self.layout().addWidget(label_widget, 0, 0)
        