"""
光标工具页面
提供坐标显示、颜色拾取、光标高亮、屏幕标尺
"""

import math

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QLabel,
    QPushButton, QSpinBox, QApplication, QFrame,
)
from PySide6.QtGui import QColor

from src.core.cursor_utils import (
    CursorTracker, CursorHighlighter,
    get_cursor_pos, get_pixel_color, rgb_to_hex,
)


class CursorToolsPage(QWidget):
    """光标工具页面"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._tracker = CursorTracker(interval_ms=50, parent=self)
        self._highlighter = CursorHighlighter()
        self._ruler_start: tuple[int, int] | None = None

        self._setup_ui()
        self._connect_signals()
        self._tracker.start()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 16, 20, 16)
        main_layout.setSpacing(12)

        title = QLabel("光标工具")
        title.setObjectName("titleLabel")
        main_layout.addWidget(title)

        # ── 实时坐标 ──
        coord_group = QGroupBox("实时坐标")
        coord_layout = QHBoxLayout(coord_group)
        coord_layout.addWidget(QLabel("屏幕坐标:"))
        self._coord_label = QLabel("(0, 0)")
        self._coord_label.setStyleSheet(
            "font-size: 16px; font-weight: bold; color: #e94560;")
        coord_layout.addWidget(self._coord_label)
        coord_layout.addStretch()
        self._copy_coord_btn = QPushButton("📋 复制坐标")
        self._copy_coord_btn.clicked.connect(self._copy_coord)
        coord_layout.addWidget(self._copy_coord_btn)
        main_layout.addWidget(coord_group)

        # ── 颜色拾取 ──
        color_group = QGroupBox("颜色拾取")
        color_layout = QHBoxLayout(color_group)
        color_layout.addWidget(QLabel("当前颜色:"))

        self._color_preview = QFrame()
        self._color_preview.setFixedSize(32, 32)
        self._color_preview.setStyleSheet(
            "background-color: #000; border: 2px solid #0f3460; border-radius: 4px;")
        color_layout.addWidget(self._color_preview)

        self._rgb_label = QLabel("RGB: (0, 0, 0)")
        color_layout.addWidget(self._rgb_label)
        self._hex_label = QLabel("HEX: #000000")
        color_layout.addWidget(self._hex_label)
        color_layout.addStretch()

        self._copy_rgb_btn = QPushButton("📋 复制 RGB")
        self._copy_rgb_btn.clicked.connect(
            lambda: self._copy_text(self._rgb_label.text().replace("RGB: ", "")))
        color_layout.addWidget(self._copy_rgb_btn)

        self._copy_hex_btn = QPushButton("📋 复制 HEX")
        self._copy_hex_btn.clicked.connect(
            lambda: self._copy_text(self._hex_label.text().replace("HEX: ", "")))
        color_layout.addWidget(self._copy_hex_btn)
        main_layout.addWidget(color_group)

        # ── 光标高亮 ──
        hl_group = QGroupBox("光标高亮")
        hl_layout = QHBoxLayout(hl_group)
        hl_layout.addWidget(QLabel("圆圈大小:"))
        self._hl_radius = QSpinBox()
        self._hl_radius.setRange(10, 200)
        self._hl_radius.setValue(30)
        self._hl_radius.setSuffix(" px")
        hl_layout.addWidget(self._hl_radius)

        self._hl_toggle_btn = QPushButton("🔴 开启高亮")
        self._hl_toggle_btn.setObjectName("dangerBtn")
        self._hl_toggle_btn.clicked.connect(self._toggle_highlight)
        hl_layout.addWidget(self._hl_toggle_btn)
        hl_layout.addStretch()
        main_layout.addWidget(hl_group)

        # ── 屏幕标尺 ──
        ruler_group = QGroupBox("屏幕标尺")
        ruler_layout = QVBoxLayout(ruler_group)
        ruler_layout.addWidget(QLabel("点击起点和终点测量像素距离"))

        btn_layout = QHBoxLayout()
        self._ruler_start_btn = QPushButton("📍 设置起点")
        self._ruler_start_btn.clicked.connect(self._set_ruler_start)
        btn_layout.addWidget(self._ruler_start_btn)
        self._ruler_end_btn = QPushButton("📍 设置终点")
        self._ruler_end_btn.clicked.connect(self._set_ruler_end)
        btn_layout.addWidget(self._ruler_end_btn)
        self._ruler_clear_btn = QPushButton("🗑️ 清除")
        self._ruler_clear_btn.clicked.connect(self._clear_ruler)
        btn_layout.addWidget(self._ruler_clear_btn)
        btn_layout.addStretch()
        ruler_layout.addLayout(btn_layout)

        self._ruler_result = QLabel("距离: -- px")
        self._ruler_result.setStyleSheet(
            "font-size: 14px; font-weight: bold; color: #2ecc71;")
        ruler_layout.addWidget(self._ruler_result)
        self._ruler_detail = QLabel("起点: (--, --) → 终点: (--, --)")
        ruler_layout.addWidget(self._ruler_detail)
        main_layout.addWidget(ruler_group)
        main_layout.addStretch()

    def _connect_signals(self):
        self._tracker.position_changed.connect(self._on_position)
        self._tracker.color_changed.connect(self._on_color)

    def _on_position(self, x: int, y: int):
        self._coord_label.setText(f"({x}, {y})")

    def _on_color(self, r: int, g: int, b: int):
        self._color_preview.setStyleSheet(
            f"background-color: rgb({r},{g},{b}); "
            f"border: 2px solid #0f3460; border-radius: 4px;")
        self._rgb_label.setText(f"RGB: ({r}, {g}, {b})")
        self._hex_label.setText(f"HEX: {rgb_to_hex(r, g, b)}")

    def _copy_coord(self):
        self._copy_text(self._coord_label.text().strip("()"))

    @staticmethod
    def _copy_text(text: str):
        QApplication.clipboard().setText(text)

    def _toggle_highlight(self):
        if self._highlighter.is_active:
            self._highlighter.stop()
            self._hl_toggle_btn.setText("🔴 开启高亮")
            self._set_btn_style(self._hl_toggle_btn, "dangerBtn")
        else:
            self._highlighter.start(radius=self._hl_radius.value())
            self._hl_toggle_btn.setText("🟢 关闭高亮")
            self._set_btn_style(self._hl_toggle_btn, "successBtn")

    def _set_ruler_start(self):
        x, y = get_cursor_pos()
        self._ruler_start = (x, y)
        self._ruler_detail.setText(f"起点: ({x}, {y}) → 终点: (--, --)")
        self._ruler_result.setText("请点击终点...")

    def _set_ruler_end(self):
        x, y = get_cursor_pos()
        start = self._ruler_start or (0, 0)
        dist = math.hypot(x - start[0], y - start[1])
        self._ruler_result.setText(f"距离: {dist:.1f} px")
        self._ruler_detail.setText(f"起点: ({start[0]}, {start[1]}) → 终点: ({x}, {y})")

    def _clear_ruler(self):
        self._ruler_start = None
        self._ruler_result.setText("距离: -- px")
        self._ruler_detail.setText("起点: (--, --) → 终点: (--, --)")

    @staticmethod
    def _set_btn_style(btn, object_name: str):
        btn.setObjectName(object_name)
        btn.style().unpolish(btn)
        btn.style().polish(btn)

    def get_params(self) -> dict:
        return {}

    def apply_params(self, params: dict):
        pass

    def cleanup(self):
        self._tracker.stop()
        if self._highlighter.is_active:
            self._highlighter.stop()
