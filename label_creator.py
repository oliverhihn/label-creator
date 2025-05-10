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
    QLineEdit,
    QPushButton,
    QSizePolicy,
)
from PyQt5.QtGui import QPixmap, QPainter, QPen, QFont, QIcon
from PyQt5.QtCore import Qt, QSize


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

            # "None" option if no icons were found
            if not found_icons:
                self.icons = ["None"]
            else:
                self.icons = found_icons

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        dim_layout = QHBoxLayout()
        dim_label = QLabel("Dimensions:")
        self.dim_combo = QComboBox()

        for dim in self.dimensions:
            self.dim_combo.addItem(f"{dim['name']} ({dim['width']}x{dim['height']})")

        dim_layout.addWidget(dim_label)
        dim_layout.addWidget(self.dim_combo)
        main_layout.addLayout(dim_layout)

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

        text_layout = QHBoxLayout()
        text_label = QLabel("Text:")
        self.text_input = QLineEdit()
        self.text_input.setText("Text here")  # Set default text

        text_layout.addWidget(text_label)
        text_layout.addWidget(self.text_input)
        main_layout.addLayout(text_layout)

        self.preview_label = QLabel()
        self.preview_label.setAlignment(Qt.AlignCenter)
        self.preview_label.setMinimumSize(400, 200)
        self.preview_label.setStyleSheet("border: 1px solid black;")
        self.preview_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        main_layout.addWidget(self.preview_label)

        button_layout = QHBoxLayout()

        preview_button = QPushButton("Preview")
        preview_button.clicked.connect(self.update_preview)

        generate_button = QPushButton("Generate Label")
        generate_button.clicked.connect(self.generate_label)

        button_layout.addWidget(preview_button)
        button_layout.addWidget(generate_button)
        main_layout.addLayout(button_layout)

        self.update_preview()

    def get_current_dimensions(self):
        index = self.dim_combo.currentIndex()
        if index >= 0 and index < len(self.dimensions):
            return self.dimensions[index]
        return {"name": "Default", "width": 400, "height": 200}

    def get_current_icon_path(self):
        icon = self.icon_combo.currentText()
        if icon == "None":
            return None
        return os.path.join("icons", icon)

    def update_preview(self):
        dimensions = self.get_current_dimensions()
        width, height = dimensions["width"], dimensions["height"]

        pixmap = QPixmap(width, height)
        pixmap.fill(Qt.white)

        painter = QPainter(pixmap)

        icon_path = self.get_current_icon_path()
        text = self.text_input.text()

        self.draw_label_content(painter, width, height, icon_path, text)

        painter.end()

        scaled_pixmap = pixmap.scaled(
            self.preview_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation
        )

        self.preview_label.setPixmap(scaled_pixmap)

    def draw_label_content(self, painter, width, height, icon_path, text):
        base_font_size = max(12, min(36, height // 8))
        font = QFont("Arial", base_font_size)
        painter.setFont(font)

        if icon_path and text:
            icon = QPixmap(icon_path)
            icon_height = height - 20
            icon_width = int(icon.width() * (icon_height / icon.height()))

            icon_x = 10
            icon_y = 10

            painter.drawPixmap(icon_x, icon_y, icon_width, icon_height, icon)

            painter.setPen(QPen(Qt.black, 2))
            line_x = icon_x + icon_width + 10
            painter.drawLine(line_x, 10, line_x, height - 10)

            text_area_width = width - line_x - 20
            text_area_height = height - 20

            font_size = self.find_optimal_font_size(
                painter, text, text_area_width, text_area_height, base_font_size
            )

            font.setPointSize(font_size)
            painter.setFont(font)

            text_rect = painter.boundingRect(
                0, 0, text_area_width, text_area_height, Qt.TextWordWrap, text
            )
            text_x = line_x + 10
            text_y = (height - text_rect.height()) // 2

            painter.drawText(
                text_x,
                text_y,
                text_area_width,
                text_rect.height(),
                Qt.TextWordWrap,
                text,
            )

        elif icon_path:
            icon = QPixmap(icon_path)
            icon_height = height - 20
            icon_width = int(icon.width() * (icon_height / icon.height()))

            icon_x = (width - icon_width) // 2
            icon_y = (height - icon_height) // 2

            painter.drawPixmap(icon_x, icon_y, icon_width, icon_height, icon)

        elif text:
            text_area_width = width - 20
            text_area_height = height - 20

            font_size = self.find_optimal_font_size(
                painter, text, text_area_width, text_area_height, base_font_size
            )

            font.setPointSize(font_size)
            painter.setFont(font)

            text_rect = painter.boundingRect(
                0, 0, text_area_width, text_area_height, Qt.TextWordWrap, text
            )

            text_x = (width - text_rect.width()) // 2
            text_y = (height - text_rect.height()) // 2

            painter.drawText(
                text_x,
                text_y,
                text_rect.width(),
                text_rect.height(),
                Qt.TextWordWrap,
                text,
            )

    def find_optimal_font_size(self, painter, text, max_width, max_height, start_size):
        """Find the largest font size that fits the text within the given dimensions."""
        font_size = start_size
        font = QFont("Arial", font_size)

        max_font_size = min(72, max_height // 2)
        increment = 2

        while font_size < max_font_size:
            font.setPointSize(font_size + increment)
            painter.setFont(font)
            text_rect = painter.boundingRect(
                0, 0, max_width, max_height, Qt.TextWordWrap, text
            )

            if text_rect.width() > max_width or text_rect.height() > max_height:
                break

            font_size += increment

        if text_rect.width() > max_width or text_rect.height() > max_height:
            font_size -= increment

        font.setPointSize(font_size)
        painter.setFont(font)
        text_rect = painter.boundingRect(
            0, 0, max_width, max_height, Qt.TextWordWrap, text
        )

        while font_size > 10 and (
            text_rect.width() > max_width or text_rect.height() > max_height
        ):
            font_size -= 1
            font.setPointSize(font_size)
            painter.setFont(font)
            text_rect = painter.boundingRect(
                0, 0, max_width, max_height, Qt.TextWordWrap, text
            )

        return font_size

    def generate_label(self):
        dimensions = self.get_current_dimensions()
        width, height = dimensions["width"], dimensions["height"]

        pixmap = QPixmap(width, height)
        pixmap.fill(Qt.white)

        painter = QPainter(pixmap)

        icon_path = self.get_current_icon_path()
        text = self.text_input.text()

        self.draw_label_content(painter, width, height, icon_path, text)

        painter.end()

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        icon_name = (
            "no_icon"
            if not icon_path
            else os.path.splitext(os.path.basename(icon_path))[0]
        )
        text_short = text[:10].replace(" ", "_") if text else "no_text"

        filename = f"label_{icon_name}_{text_short}_{timestamp}.png"
        output_path = os.path.join("output", filename)

        os.makedirs("output", exist_ok=True)

        if pixmap.save(output_path):
            print(f"Label saved to {output_path}")
            self.statusBar().showMessage(f"Label saved to {output_path}", 3000)
        else:
            print("Failed to save the label")
            self.statusBar().showMessage("Failed to save the label", 3000)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = LabelCreator()
    window.show()
    sys.exit(app.exec_())
