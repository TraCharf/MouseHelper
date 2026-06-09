"""
左侧导航栏组件
"""

from PySide6.QtCore import Signal, Qt
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, QButtonGroup, QSpacerItem, QSizePolicy
)


class SidebarButton(QPushButton):
    """侧边栏导航按钮"""

    def __init__(self, text: str, icon_text: str = "", checkable: bool = True, parent=None):
        super().__init__(parent)
        self.setText(f"{icon_text}\n{text}" if icon_text else text)
        self.setCheckable(checkable)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setMinimumHeight(52)
        self.setMaximumWidth(60)


class Sidebar(QWidget):
    """左侧导航栏"""

    page_changed = Signal(int)
    about_clicked = Signal()
    exit_clicked = Signal()

    PAGES = [
        ("🖱️", "连点器"),
        ("⏺️", "录制"),
        ("📝", "宏编辑"),
        ("🔧", "工具"),
        ("📂", "预设"),
        ("⚙️", "设置"),
    ]

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("sidebar")
        self.setFixedWidth(66)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 10, 4, 10)
        layout.setSpacing(2)

        self._button_group = QButtonGroup(self)
        self._button_group.setExclusive(True)

        for i, (icon, name) in enumerate(self.PAGES):
            btn = SidebarButton(name, icon)
            btn.clicked.connect(lambda checked, idx=i: self.page_changed.emit(idx))
            layout.addWidget(btn)
            self._button_group.addButton(btn, i)
            if i == 0:
                btn.setChecked(True)

        layout.addSpacerItem(QSpacerItem(20, 20, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))

        # ── 底部按钮（不可选中） ──
        about_btn = SidebarButton("关于", "ℹ️", checkable=False)
        about_btn.clicked.connect(self.about_clicked.emit)
        layout.addWidget(about_btn)

        exit_btn = SidebarButton("退出", "⏻", checkable=False)
        exit_btn.setObjectName("dangerBtn")
        exit_btn.clicked.connect(self.exit_clicked.emit)
        layout.addWidget(exit_btn)

    def set_current_index(self, index: int):
        if 0 <= index < len(self.PAGES):
            button = self._button_group.button(index)
            if button:
                button.setChecked(True)
