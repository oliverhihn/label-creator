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
    QCheckBox,
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
                data: dict = yaml.safe_load(file)
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
            if icon != "None":
                icon_path = os.path.join("icons", icon)
                self.icon_combo.addItem(QIcon(icon_path), icon)

        if self.icons:
            self.icon_combo.insertSeparator(self.icon_combo.count())
        self.icon_combo.addItem("None")
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

        # Padding checkbox
        padding_layout = QHBoxLayout()
        self.padding_check = QCheckBox("Padding")
        self.padding_check.setChecked(False)
        padding_layout.addWidget(self.padding_check)
        main_layout.addLayout(padding_layout)

        # Preview area
        self.preview_label = QLabel()
        # Remove fixed minimums and let it expand to fill
        self.preview_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.preview_label.setAlignment(Qt.AlignCenter)
        # Add with stretch=1 so it takes remaining space
        main_layout.addWidget(self.preview_label, 1)

        # Buttons
        button_layout = QHBoxLayout()
        generate_button = QPushButton("Generate Label")
        generate_button.clicked.connect(self.generate_label)
        button_layout.addWidget(generate_button)
        main_layout.addLayout(button_layout)

        # Auto-update
        self.dim_combo.currentIndexChanged.connect(self.update_preview)
        self.icon_combo.currentIndexChanged.connect(self.update_preview)
        self.text_input.textChanged.connect(self.update_preview)
        self.padding_check.stateChanged.connect(self.update_preview)

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
        # Get selected dimensions
        dims = self.get_current_dimensions()
        width_val, h = dims.get("width"), dims.get("height")
        # Determine padding margin
        use_padding = self.padding_check.isChecked()
        pad = 10 if use_padding else 0
        # Handle dynamic width (auto): fit font to height, then compute width
        if isinstance(width_val, str) and width_val.lower() == "auto":
            # Temp painter for measurements
            temp_pix = QPixmap(1, 1)
            temp_painter = QPainter(temp_pix)
            # Compute optimal font size by height only (large max_w)
            base_size = max(12, min(36, h // 8))
            temp_painter.setFont(QFont("Arial", base_size))
            # find size using a very large max_w
            size = self.find_optimal_font_size_no_wrap(
                temp_painter,
                self.text_input.toPlainText().rstrip("\n").split("\n"),
                max_w=10**9,
                max_h=h - pad * 2,
                start=base_size,
            )
            font = QFont("Arial", size)
            temp_painter.setFont(font)
            fm = temp_painter.fontMetrics()
            text = self.text_input.toPlainText().rstrip("\n") or ""
            lines = text.split("\n")
            text_max_w = max((fm.horizontalAdvance(line) for line in lines), default=0)
            icon_path = self.get_current_icon_path()
            # Calculate final width including icon and padding
            if icon_path and text:
                icon = QPixmap(icon_path)
                icon_h = h - pad * 2
                icon_w = int(icon.width() * (icon_h / icon.height()))
                w = pad + icon_w + pad + text_max_w + pad
            else:
                w = text_max_w + pad * 2
            temp_painter.end()
        else:
            w = width_val

        # Ensure width is integer
        if not isinstance(w, int):
            try:
                w = int(w)
            except ValueError:
                w = 0
        # Create a new pixmap at the actual dimensions
        pix = QPixmap(w, h)
        pix.fill(Qt.white)
        painter = QPainter(pix)
        painter.setRenderHint(QPainter.TextAntialiasing)

        icon_path = self.get_current_icon_path()
        text = self.text_input.toPlainText().rstrip("\n")
        use_padding = self.padding_check.isChecked()
        self.draw_label_content(painter, w, h, icon_path, text, use_padding)

        painter.end()

        max_preview_width = self.preview_label.width()
        max_preview_height = self.preview_label.height()

        # Create a new clean pixmap for the preview with the exact scaled size
        scaled = pix.scaled(
            max_preview_width,
            max_preview_height,
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation,
        )

        # Clear any previous content and set the fresh scaled pixmap
        self.preview_label.clear()
        self.preview_label.setPixmap(scaled)

    def draw_label_content(
        self,
        painter: QPainter,
        width: int,
        height: int,
        icon_path: str,
        text: str,
        padding: bool = False,
    ):
        base_size = max(12, min(36, height // 8))
        font = QFont("Arial", base_size)
        painter.setFont(font)

        # Determine padding margin
        pad = 10 if padding else 0
        # Prepare lines
        lines = text.split("\n") if text else []

        if icon_path and lines:
            # Draw icon
            icon = QPixmap(icon_path)
            icon_h = height - pad * 2
            icon_w = int(icon.width() * (icon_h / icon.height()))
            icon_x, icon_y = pad, pad
            painter.drawPixmap(icon_x, icon_y, icon_w, icon_h, icon)

            # Divider
            painter.setPen(QPen(Qt.black, 2))
            line_x = icon_x + icon_w + pad
            painter.drawLine(line_x, pad, line_x, height - pad)

            # Text area
            area_x, area_y = line_x + 10, pad
            area_w, area_h = width - area_x - pad, height - pad * 2

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
            icon_h = height - pad * 2
            icon_w = int(icon.width() * (icon_h / icon.height()))
            painter.drawPixmap(
                (width - icon_w) // 2, (height - icon_h) // 2, icon_w, icon_h, icon
            )

        elif lines:
            # Text-only area
            area_x, area_y = pad, pad
            area_w, area_h = width - pad * 2, height - pad * 2

            size = self.find_optimal_font_size_no_wrap(
                painter, lines, area_w, area_h, base_size
            )
            font.setPointSize(size)
            painter.setFont(font)

            rect = QRect(area_x, area_y, area_w, area_h)
            painter.drawText(rect, Qt.AlignHCenter | Qt.AlignVCenter, text)

    def find_optimal_font_size_no_wrap(
        self, painter: QPainter, lines: list, max_w: int, max_h: int, start: int
    ):
        # Determine vertical limit: full height for single line, else divide by lines+1
        height_limit = max_h if len(lines) == 1 else max_h // (len(lines) + 1)
        # For single-line, start at full available height; for multi-line, start at provided start size
        if len(lines) == 1:
            size = height_limit
        else:
            size = start
        font = painter.font()
        font.setPointSize(size)
        painter.setFont(font)
        # Increase until overflow only for multi-line
        if len(lines) != 1:
            while True:
                next_size = size + 2
                # Stop if next size exceeds vertical limit
                if next_size > height_limit:
                    break
                font.setPointSize(next_size)
                painter.setFont(font)
                fm = painter.fontMetrics()
                # Break on any overflow
                if fm.height() * len(lines) > max_h or any(
                    fm.horizontalAdvance(line) > max_w for line in lines
                ):
                    break
                size = next_size
        # Decrease if necessary
        font.setPointSize(size)
        painter.setFont(font)
        fm = painter.fontMetrics()
        while size > 10 and (
            fm.height() * len(lines) > max_h
            or any(fm.horizontalAdvance(line) > max_w for line in lines)
        ):
            size -= 1
            font.setPointSize(size)
            painter.setFont(font)
            fm = painter.fontMetrics()
        return size

    def generate_label(self):
        dims = self.get_current_dimensions()
        width_val, h = dims.get("width"), dims.get("height")
        # Determine padding margin
        use_padding = self.padding_check.isChecked()
        pad = 10 if use_padding else 0
        # Handle dynamic width (auto)
        if isinstance(width_val, str) and width_val.lower() == 'auto':
            temp_pix = QPixmap(1, 1)
            temp_painter = QPainter(temp_pix)
            base_size = max(12, min(36, h // 8))
            temp_painter.setFont(QFont("Arial", base_size))
            size = self.find_optimal_font_size_no_wrap(
                temp_painter,
                self.text_input.toPlainText().rstrip("\n").split("\n"),
                max_w=10**9,
                max_h=h - pad * 2,
                start=base_size,
            )
            font = QFont("Arial", size)
            temp_painter.setFont(font)
            fm = temp_painter.fontMetrics()
            text = self.text_input.toPlainText().rstrip("\n") or ""
            lines = text.split("\n")
            text_max_w = max((fm.horizontalAdvance(line) for line in lines), default=0)
            icon_path = self.get_current_icon_path()
            if icon_path and text:
                icon = QPixmap(icon_path)
                icon_h = h - pad * 2
                icon_w = int(icon.width() * (icon_h / icon.height()))
                w = pad + icon_w + pad + text_max_w + pad
            else:
                w = text_max_w + pad * 2
            temp_painter.end()
        else:
            w = width_val
        # Ensure width is integer
        try:
            w = int(w)
        except Exception:
            w = 0
        pix = QPixmap(w, h)
        pix.fill(Qt.white)
        painter = QPainter(pix)
        painter.setRenderHint(QPainter.TextAntialiasing)

        icon_path = self.get_current_icon_path()
        text = self.text_input.toPlainText().rstrip("\n")
        use_padding = self.padding_check.isChecked()
        self.draw_label_content(painter, w, h, icon_path, text, use_padding)

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
    window.statusBar().showMessage("")
    sys.exit(app.exec_())
