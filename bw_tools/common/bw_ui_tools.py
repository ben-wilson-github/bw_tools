from PySide2.QtCore import Qt
from PySide2.QtGui import QFont
from PySide2.QtWidgets import QLabel


def label(
    text, alignment=Qt.AlignCenter, bold=True, dimmed=True, tabbed=False
) -> QLabel:
    if tabbed:
        text = f"\t{text}"

    w = QLabel(text)

    if bold:
        font = QFont()
        font.setBold(True)
        w.setFont(font)

    if alignment:
        w.setAlignment(alignment)

    if dimmed:
        w.setStyleSheet("color : gray")

    return w


def separator(orientation="h") -> QLabel:
    w = QLabel()
    if orientation == "h":
        w.setFixedHeight(1)
    elif orientation == "v":
        w.setFixedWidth(1)
    # w.setStyleSheet('background : #151515')
    w.setStyleSheet("background : #353535")
    return w
