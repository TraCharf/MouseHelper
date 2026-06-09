"""
主窗口框架
侧边栏 + QStackedWidget 页面切换 + 状态栏 + 系统托盘
"""

import pyautogui
from PySide6.QtCore import QTimer
from PySide6.QtGui import QCursor
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QStackedWidget,
    QStatusBar, QLabel, QMessageBox, QApplication, QGroupBox,
)

from src.ui.sidebar import Sidebar
from src.ui.auto_clicker import AutoClickerPage
from src.ui.recorder import RecorderPage
from src.ui.macro_editor import MacroEditorPage
from src.ui.cursor_tools import CursorToolsPage
from src.ui.preset_manager import PresetManagerPage
from src.ui.tray_manager import TrayManager
from src.core.hotkey_engine import hotkey_engine
from src.data.config import config


class SettingsPage(QWidget):
    """设置页面"""

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(12)

        title = QLabel("设置")
        title.setObjectName("titleLabel")
        layout.addWidget(title)

        general_group = QGroupBox("常规设置")
        gl = QVBoxLayout(general_group)
        gl.addWidget(QLabel("配置目录: " + str(config.data_dir)))
        gl.addWidget(QLabel("关闭窗口时最小化到托盘: " +
                            ("是" if config.get("general", "close_to_tray", default=True) else "否")))
        layout.addWidget(general_group)

        hotkey_group = QGroupBox("全局热键")
        hl = QVBoxLayout(hotkey_group)
        labels = {
            "clicker_toggle": "连点器启停",
            "recorder_toggle": "录制启停",
            "player_toggle": "回放启停",
            "emergency_stop": "紧急停止",
        }
        for action, hk in config.get("hotkeys", default={}).items():
            hl.addWidget(QLabel(f"{labels.get(action, action)}: [{hk.upper()}]"))
        layout.addWidget(hotkey_group)
        layout.addStretch()

    def get_params(self) -> dict:
        return {}

    def apply_params(self, params: dict):
        pass

    def cleanup(self):
        pass


class MainWindow(QMainWindow):
    """主窗口"""

    PAGE_NAMES = ["clicker", "player", "macro", "cursor", "preset", "settings"]

    def __init__(self):
        super().__init__()
        self.setWindowTitle("🖱️ 鼠标控制助手")
        self.setMinimumSize(800, 600)
        self.resize(900, 650)

        # 创建各页面
        self._pages: list = [
            AutoClickerPage(),
            RecorderPage(),
            MacroEditorPage(),
            CursorToolsPage(),
            PresetManagerPage(),
            SettingsPage(),
        ]

        # 预设信号
        self._pages[4].preset_loaded.connect(self._apply_preset)
        self._pages[4].save_requested.connect(self._save_current_preset)

        self._setup_ui()
        self._setup_tray()
        self._setup_statusbar()
        self._register_emergency_stop()

        if config.get("general", "start_minimized", default=False):
            self.hide()
        else:
            self.show()

    # ═══════════════════════════════════════════
    # UI 构建
    # ═══════════════════════════════════════════

    def _setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        self._sidebar = Sidebar()
        self._sidebar.page_changed.connect(self._on_page_changed)
        self._sidebar.about_clicked.connect(self._show_about)
        self._sidebar.exit_clicked.connect(self._confirm_exit)
        main_layout.addWidget(self._sidebar)

        self._stack = QStackedWidget()
        for page in self._pages:
            self._stack.addWidget(page)
        main_layout.addWidget(self._stack, 1)

    def _setup_tray(self):
        self._tray = TrayManager(self)
        self._tray.show_window.connect(self._show_from_tray)
        self._tray.quit_app.connect(self._confirm_exit)
        self._tray.toggle_clicker.connect(self._toggle_clicker_from_tray)
        self._tray.show_about.connect(self._show_about)
        self._tray.show()

    def _setup_statusbar(self):
        self._statusbar = QStatusBar()
        self.setStatusBar(self._statusbar)
        self._status_label = QLabel("🟢 就绪")
        self._statusbar.addWidget(self._status_label)

        self._coord_widget = QLabel("鼠标: (0, 0)")
        self._statusbar.addPermanentWidget(self._coord_widget)

        self._hotkey_hint = QLabel("F6 连点 | F7 录制 | F8 回放 | Esc 停止")
        self._statusbar.addPermanentWidget(self._hotkey_hint)

        self._coord_timer = QTimer(self)
        self._coord_timer.timeout.connect(self._update_coord)
        self._coord_timer.start(100)

    # ═══════════════════════════════════════════
    # 事件处理
    # ═══════════════════════════════════════════

    def _update_coord(self):
        # 使用 pyautogui 保持与点击引擎一致的坐标系统
        pos = pyautogui.position()
        self._coord_widget.setText(f"鼠标: ({pos.x}, {pos.y})")

    def _on_page_changed(self, index: int):
        self._stack.setCurrentIndex(index)

    def _show_from_tray(self):
        self.show()
        self.raise_()
        self.activateWindow()

    def _toggle_clicker_from_tray(self):
        self._pages[0]._toggle_clicker()

    def _show_about(self):
        """显示关于对话框"""
        QMessageBox.about(
            self, "关于 鼠标控制助手",
            "<h2>🖱️ 鼠标控制助手 v1.0</h2>"
            "<p>一款功能齐全、适合小白使用的鼠标控制工具</p>"
            "<hr>"
            "<p><b>开发:</b> Fng</p>"
            "<p><b>官网:</b> <a href='https://888124.xyz'>https://888124.xyz</a></p>"
            "<hr>"
            "<p style='color:#888;'>全局热键: F6 连点 | F7 录制 | F8 回放 | Esc 停止</p>"
            "<p style='color:#888;'>需要管理员权限才能使用全局热键</p>",
        )

    def _confirm_exit(self):
        """确认退出程序"""
        reply = QMessageBox.question(
            self, "确认退出", "确定要退出鼠标控制助手吗？\n\n"
            "退出后全局热键将停止工作。",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            self._cleanup_all()
            QApplication.quit()

    # ═══════════════════════════════════════════
    # 预设
    # ═══════════════════════════════════════════

    def _apply_preset(self, params: dict):
        for page in self._pages:
            if hasattr(page, 'apply_params') and params:
                page.apply_params(params)

    def gather_all_params(self) -> dict:
        all_params = {}
        for i, page in enumerate(self._pages):
            name = self.PAGE_NAMES[i] if i < len(self.PAGE_NAMES) else f"page_{i}"
            if hasattr(page, 'get_params'):
                all_params[name] = page.get_params()
        return all_params

    def _save_current_preset(self, name: str, description: str = ""):
        from src.data.preset_store import preset_store
        preset_store.save_preset(name, self.gather_all_params(), description)

    # ═══════════════════════════════════════════
    # 紧急停止
    # ═══════════════════════════════════════════

    def _register_emergency_stop(self):
        hotkey_engine.register(
            "emergency_stop",
            config.get("hotkeys", "emergency_stop", default="esc"),
            self._emergency_stop,
        )

    def _emergency_stop(self):
        for page in self._pages:
            if hasattr(page, '_engine') and page._engine:
                page._engine.stop()
                page._engine = None
            if hasattr(page, '_player') and page._player:
                page._player.stop()
                page._player = None
            if hasattr(page, '_recorder') and page._recorder.is_recording:
                page._recorder.stop()
        self._status_label.setText("⏹️ 已紧急停止")
        self._tray.show_message("鼠标控制助手", "所有操作已紧急停止")

    # ═══════════════════════════════════════════
    # 生命周期
    # ═══════════════════════════════════════════

    def _cleanup_all(self):
        for page in self._pages:
            if hasattr(page, 'save_settings'):
                page.save_settings()
            if hasattr(page, 'cleanup'):
                page.cleanup()
        hotkey_engine.unregister_all()
        if hasattr(self, '_coord_timer'):
            self._coord_timer.stop()

    def closeEvent(self, event):
        if config.get("general", "close_to_tray", default=True):
            self.hide()
            self._tray.show_message("鼠标控制助手", "程序已最小化到系统托盘，双击图标恢复窗口")
            event.ignore()
        else:
            reply = QMessageBox.question(
                self, "确认退出", "确定要退出鼠标控制助手吗？",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            if reply == QMessageBox.StandardButton.Yes:
                self._cleanup_all()
                event.accept()
            else:
                event.ignore()
