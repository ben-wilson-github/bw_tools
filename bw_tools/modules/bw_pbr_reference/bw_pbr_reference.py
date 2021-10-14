from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Dict

from bw_tools.common import bw_ui_tools
from PySide2.QtCore import Qt
from PySide2.QtGui import QCursor, QMouseEvent, QPixmap
from PySide2.QtWidgets import (
    QApplication,
    QColorDialog,
    QDialog,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLayout,
    QVBoxLayout,
    QWidget,
)

if TYPE_CHECKING:
    from bw_tools.common.bw_api_tool import BWAPITool


class BWColorPicker(QColorDialog):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setWindowFlags(Qt.WindowStaysOnTopHint)


class BWPBRReference(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setModal(False)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.widget_show_style = """
            background : #252525;
         """
        self.widget_hide_style = """
                background : transparent;
        """
        self.nonmetal_base_color = {
            "Coal": "#ff323232",
            "dark_soil": "#ff434343",
            "worn_asphalt": "#ff5c5c5c",
            "tree_bark": "#ff696969",
            "grey_plaster": "#ff818181",
            "brick": "#ff838383",
            "old_concrete": "#ff878787",
            "sand": "#ffa6a6a6",
            "clean_cement": "#ffb5b5b5",
            "snow": "#fff3f3f3",
        }
        self.metal_base_color = {
            "gold": "#ffffe29b",
            "silver": "#fffcfaf5",
            "aluminum": "#fff5f6f6",
            "iron": "#ffc4c7c7",
            "copper": "#fffad0c0",
            "chromium": "#ffc3c5c4",
            "titanium": "#ffc1bab1",
            "nickel": "#ffd3cbbe",
            "cobalt": "#ffd3d2cf",
            "platinum": "#ffd5d0c8",
        }

        self.nonmetal_base_color_widgets = {}
        self.metal_base_color_widgets = {}

        self.leftClick = False
        self.click_x = 0
        self.click_y = 0
        self.nonmetal_roughness_image_path = Path(__file__).parent / "resources" / "roughness_nonmetal.png"
        self.metal_roughness_image_path = Path(__file__).parent / "resources" / "roughness_metal.png"
        self.close_button_image_path = Path(__file__).parent / "resources" / "icons" / "close_button.png"

        self.swatch_size = 50
        self._ui()
        self.adjustSize()
        self.main_frame.setStyleSheet(self.widget_show_style)

    def mousePressEvent(self, event):
        super().mousePressEvent(event)
        self.click_x = event.x()
        self.click_y = event.y()
        if event.button() == Qt.LeftButton:
            self.leftClick = True

    def mouseMoveEvent(self, event: QMouseEvent):
        super().mouseMoveEvent(event)
        if self.leftClick:
            self.move(event.globalX() - self.click_x, event.globalY() - self.click_y)

    def mouseReleaseEvent(self, event: QMouseEvent):
        super().mouseReleaseEvent(event)
        self.leftClick = False

    def _close_window(self, _):
        self.close()

    def _on_mouse_pressed_swatch(self, event: QMouseEvent):
        pos = QCursor.pos()
        if event.button() == Qt.LeftButton:
            self.main_frame.setStyleSheet(self.widget_hide_style)
            for widget in self.main_frame.findChildren(QWidget):
                if widget == QApplication.widgetAt(pos):
                    continue
                size_policy = widget.sizePolicy()
                size_policy.setRetainSizeWhenHidden(True)
                widget.setSizePolicy(size_policy)
                widget.hide()
            self.mousePressEvent(event)

    def _on_mouse_release_swatch(self, event: QMouseEvent):
        self.main_frame.setStyleSheet(self.widget_show_style)
        pos = QCursor.pos()
        for widget in self.main_frame.findChildren(QWidget):
            if widget == QApplication.widgetAt(pos):
                continue
            size_policy = widget.sizePolicy()
            size_policy.setRetainSizeWhenHidden(True)
            widget.setSizePolicy(size_policy)
            widget.show()
        self.mouseReleaseEvent(event)

    def _ui_create_swatches(self, color_swatches: Dict, layout: QLayout):
        for i, (name, color) in enumerate(color_swatches.items()):
            color_widget = QLabel()
            # color_widget.setFixedSize(self.swatch_size, self.swatch_size / 2)
            color_widget.setFixedHeight(self.swatch_size / 1.5)
            color_widget.setStyleSheet(f"background-color : {color};")
            color_widget.mousePressEvent = self._on_mouse_pressed_swatch
            color_widget.mouseReleaseEvent = self._on_mouse_release_swatch
            layout.addWidget(color_widget, 0, i)

            pretty_name = name.replace("_", " ")
            name_widget = QLabel(pretty_name.title())
            name_widget.setFixedWidth(self.swatch_size)
            name_widget.setWordWrap(True)
            name_widget.setAlignment(Qt.AlignCenter)
            name_widget.setStyleSheet("color : gray;")
            layout.addWidget(name_widget, 1, i)

    def _ui_nonmetal_base_colors(self):
        layout = QGridLayout()
        self._ui_create_swatches(self.nonmetal_base_color, layout)
        return layout

    def _ui_metal_base_colors(self):
        layout = QGridLayout()
        self._ui_create_swatches(self.metal_base_color, layout)
        return layout

    def _ui(self):
        layout = QVBoxLayout()
        self.setLayout(layout)
        self.main_frame = QWidget()

        layout.addWidget(self.main_frame)

        self.main_layout = QVBoxLayout()
        self.main_frame.setLayout(self.main_layout)

        layout = QHBoxLayout()
        self.main_layout.addLayout(layout)

        layout.addStretch()
        pixmap = QPixmap(str(self.close_button_image_path.resolve()))
        pixmap = pixmap.scaled(15, 15, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.close_button = QLabel()
        self.close_button.setPixmap(pixmap)
        self.close_button.mouseReleaseEvent = self._close_window
        layout.addWidget(self.close_button)

        self.main_layout.addWidget(bw_ui_tools.label("Base Color (Medium Luminosity)"))
        self.main_layout.addLayout(self._ui_nonmetal_base_colors())
        self.main_layout.addLayout(self._ui_metal_base_colors())

        self.main_layout.addWidget(bw_ui_tools.separator())

        self.main_layout.addWidget(bw_ui_tools.label("Roughness"))
        pixmap_scale = (self.swatch_size * 10) + (9 * 5)
        pixmap = QPixmap(str(self.nonmetal_roughness_image_path.resolve()))
        pixmap = pixmap.scaled(
            pixmap_scale,
            pixmap_scale,
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation,
        )
        nonmetal_roughness = QLabel()
        nonmetal_roughness.setPixmap(pixmap)
        self.main_layout.addWidget(nonmetal_roughness)
        gradient_widget = QLabel()
        gradient_style = """
            background : qlineargradient(x1:0 y1:0, x2:1 y2:0, stop:0 black, stop:1 white);
        """
        gradient_widget.setStyleSheet(gradient_style)
        gradient_widget.setFixedHeight(self.swatch_size / 1.5)
        self.main_layout.addWidget(gradient_widget)
        pixmap = QPixmap(str(self.metal_roughness_image_path.resolve()))
        pixmap = pixmap.scaled(
            pixmap_scale,
            pixmap_scale,
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation,
        )
        metal_roughness = QLabel()
        metal_roughness.setPixmap(pixmap)
        self.main_layout.addWidget(metal_roughness)

        self.main_layout.addWidget(bw_ui_tools.separator())


def open_pbr_chart(api: BWAPITool):
    api.log.info("Opening PBR reference window")

    pbr_reference_dialog = BWPBRReference(parent=None)
    pbr_reference_dialog.show()


def on_initialize(api: BWAPITool):
    action = api.menu.addAction("Open PBR Chart")
    action.triggered.connect(lambda: open_pbr_chart(api))
