from PySide2 import QtCore
from PySide2 import QtGui
from PySide2 import QtWidgets


def label(text, alignment=QtCore.Qt.AlignCenter, bold=True, dimmed=True, tabbed=False):
    if tabbed:
        text = f'\t{text}'

    w = QtWidgets.QLabel(text)

    if bold:
        font = QtGui.QFont()
        font.setBold(True)
        w.setFont(font)

    if alignment:
        w.setAlignment(alignment)

    if dimmed:
        w.setStyleSheet('color : gray')

    return w


def separator_frame(orientation='h'):
    line = QtWidgets.QFrame()
    if orientation == 'h':
        line.setFrameShape(QtWidgets.QFrame.HLine)
    elif orientation == 'v':
        line.setFrameShape(QtWidgets.QFrame.VLine)
    line.setFrameShadow(QtWidgets.QFrame.Sunken)
    return line

def separator(orientation='h'):
    w = QtWidgets.QLabel()
    if orientation == 'h':
        w.setFixedHeight(1)
    elif orientation == 'v':
        w.setFixedWidth(1)
    # w.setStyleSheet('background : #151515')
    w.setStyleSheet('background : #353535')
    return w


