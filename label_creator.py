#!/usr/bin/env python3
import sys
import os
import yaml
from datetime import datetime
from PyQt5.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QComboBox,
    QLabel,
    QPushButton,
    QSizePolicy,
    QTextEdit,
)
from PyQt5.QtGui import QPixmap, QPainter, QPen, QFont, QIcon
from PyQt5.QtCore import Qt, QSize, QRect


class LabelCreator(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Label Creator")
        self.setGeometry(100, 100, 800, 600)

        self.dimensions = []
        self.load_dimensions()

        self.icons = []
        self.scan_icons()

        self.init_ui()

    def load_dimensions(self):
        try:
            with open("dimensions.yaml", "r") as file:
                data = yaml.safe_load(file)
                self.dimensions = data.get("dimensions", [])
        except Exception as e:
            print(f"Error loading dimensions: {e}")
            self.dimensions = [{"name": "Default", "width": 400, "height": 200}]

    def scan_icons(self):
        icons_dir = "icons"
        if os.path.exists(icons_dir):
            found_icons = []
            for file in os.listdir(icons_dir):
                if file.lower().endswith((".svg", ".png", ".jpg", ".jpeg")):
                    found_icons.append(file)
            self.icons = found_icons or ["None"]

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # Dimensions selector
        dim_layout = QHBoxLayout()
        dim_label = QLabel("Dimensions:")
        self.dim_combo = QComboBox()
        for dim in self.dimensions:
            self.dim_combo.addItem(f"{dim['name']} ({dim['width']}x{dim['height']})")
        dim_layout.addWidget(dim_label)
        dim_layout.addWidget(self.dim_combo)
        main_layout.addLayout(dim_layout)

        # Icon selector
        icon_layout = QHBoxLayout()
        icon_label = QLabel("Icon:")
        self.icon_combo = QComboBox()
        self.icon_combo.setIconSize(QSize(24, 24))
        for icon in self.icons:
            if icon == "None":
                self.icon_combo.addItem("None")
            else:
                icon_path = os.path.join("icons", icon)
                self.icon_combo.addItem(QIcon(icon_path), icon)
        icon_layout.addWidget(icon_label)
        icon_layout.addWidget(self.icon_combo)
        main_layout.addLayout(icon_layout)

        # Text input
        text_layout = QHBoxLayout()
        text_label = QLabel("Text:")
        self.text_input = QTextEdit()
        self.text_input.setText("Text here")
        self.text_input.setMinimumHeight(80)
        text_layout.addWidget(text_label)
        text_layout.addWidget(self.text_input)
        main_layout.addLayout(text_layout)

        # Preview area
        self.preview_label = QLabel()
        self.preview_label.setAlignment(Qt.AlignCenter)
        self.preview_label.setMinimumSize(400, 200)
        self.preview_label.setStyleSheet("border: 1px solid black;")
        self.preview_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        main_layout.addWidget(self.preview_label)

        # Buttons
        button_layout = QHBoxLayout()
        preview_button = QPushButton("Update Preview")
        preview_button.clicked.connect(self.update_preview)
        generate_button = QPushButton("Generate Label")
        generate_button.clicked.connect(self.generate_label)
        button_layout.addWidget(preview_button)
        button_layout.addWidget(generate_button)
        main_layout.addLayout(button_layout)

        # Auto-update
        self.dim_combo.currentIndexChanged.connect(self.update_preview)
        self.icon_combo.currentIndexChanged.connect(self.update_preview)
        self.text_input.textChanged.connect(self.update_preview)

        # Initial render
        self.update_preview()

    def get_current_dimensions(self):
        idx = self.dim_combo.currentIndex()
        return (
            self.dimensions[idx]
            if 0 <= idx < len(self.dimensions)
            else {"name": "Default", "width": 400, "height": 200}
        )

    def get_current_icon_path(self):
        icon = self.icon_combo.currentText()
        return None if icon == "None" else os.path.join("icons", icon)

    def update_preview(self):
        dims = self.get_current_dimensions()
        w, h = dims["width"], dims["height"]
        pix = QPixmap(w, h)
        pix.fill(Qt.white)
        painter = QPainter(pix)
        painter.setRenderHint(QPainter.TextAntialiasing)

        icon_path = self.get_current_icon_path()
        text = self.text_input.toPlainText().rstrip("\n")
        self.draw_label_content(painter, w, h, icon_path, text)

        painter.end()
        scaled = pix.scaled(
            self.preview_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation
        )
        self.preview_label.setPixmap(scaled)

    def draw_label_content(self, painter, width, height, icon_path, text):
        base_size = max(12, min(36, height // 8))
        font = QFont("Arial", base_size)
        painter.setFont(font)

        # Prepare lines
        lines = text.split("\n") if text else []

        if icon_path and lines:
            # Draw icon
            icon = QPixmap(icon_path)
            icon_h = height - 20
            icon_w = int(icon.width() * (icon_h / icon.height()))
            icon_x, icon_y = 10, 10
            painter.drawPixmap(icon_x, icon_y, icon_w, icon_h, icon)

            # Divider
            painter.setPen(QPen(Qt.black, 2))
            line_x = icon_x + icon_w + 10
            painter.drawLine(line_x, 10, line_x, height - 10)

            # Text area
            area_x, area_y = line_x + 10, 10
            area_w, area_h = width - area_x - 10, height - 20

            # Optimal font size
            size = self.find_optimal_font_size_no_wrap(
                painter, lines, area_w, area_h, base_size
            )
            font.setPointSize(size)
            painter.setFont(font)

            # Draw centered vertically
            rect = QRect(area_x, area_y, area_w, area_h)
            painter.drawText(rect, Qt.AlignLeft | Qt.AlignVCenter, text)

        elif icon_path:
            icon = QPixmap(icon_path)
            icon_h = height - 20
            icon_w = int(icon.width() * (icon_h / icon.height()))
            painter.drawPixmap(
                (width - icon_w) // 2, (height - icon_h) // 2, icon_w, icon_h, icon
            )

        elif lines:
            # Text-only area
            area_x, area_y = 10, 10
            area_w, area_h = width - 20, height - 20

            size = self.find_optimal_font_size_no_wrap(
                painter, lines, area_w, area_h, base_size
            )
            font.setPointSize(size)
            painter.setFont(font)

            rect = QRect(area_x, area_y, area_w, area_h)
            painter.drawText(rect, Qt.AlignHCenter | Qt.AlignVCenter, text)

    def find_optimal_font_size_no_wrap(self, painter, lines, max_w, max_h, start):
        size = start
        font = painter.font()
        font.setPointSize(size)
        painter.setFont(font)
        fm = painter.fontMetrics()
        # Increase until overflow
        while size < min(72, max_h // (len(lines) + 1)):
            font.setPointSize(size + 2)
            painter.setFont(font)
            fm = painter.fontMetrics()
            if fm.height() * len(lines) > max_h or any(
                fm.horizontalAdvance(l) > max_w for l in lines
            ):
                break
            size += 2
        # Decrease if necessary
        font.setPointSize(size)
        painter.setFont(font)
        fm = painter.fontMetrics()
        while size > 10 and (
            fm.height() * len(lines) > max_h
            or any(fm.horizontalAdvance(l) > max_w for l in lines)
        ):
            size -= 1
            font.setPointSize(size)
            painter.setFont(font)
            fm = painter.fontMetrics()
        return size

    def generate_label(self):
        dims = self.get_current_dimensions()
        w, h = dims["width"], dims["height"]
        pix = QPixmap(w, h)
        pix.fill(Qt.white)
        painter = QPainter(pix)
        painter.setRenderHint(QPainter.TextAntialiasing)

        icon_path = self.get_current_icon_path()
        text = self.text_input.toPlainText().rstrip("\n")
        self.draw_label_content(painter, w, h, icon_path, text)

        painter.end()

        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        icon_name = (
            "no_icon"
            if not icon_path
            else os.path.splitext(os.path.basename(icon_path))[0]
        )
        txt = text[:10].replace(" ", "_") if text else "no_text"
        fn = f"label_{icon_name}_{txt}_{ts}.png"
        op = os.path.join("output", fn)
        os.makedirs("output", exist_ok=True)
        if pix.save(op):
            print(f"Label saved to {op}")
            self.statusBar().showMessage(f"Label saved to {op}", 3000)
        else:
            print("Failed to save the label")
            self.statusBar().showMessage("Failed to save the label", 3000)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = LabelCreator()
    window.show()
    # init status bar
    window.statusBar().showMessage("")
    sys.exit(app.exec_())
