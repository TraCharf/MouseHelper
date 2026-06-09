"""
系统托盘管理器
支持最小化到托盘、托盘菜单、气泡提示
"""

from PySide6.QtCore import QObject, Signal
from PySide6.QtGui import QIcon, QAction
from PySide6.QtWidgets import QSystemTrayIcon, QMenu, QApplication


class TrayManager(QObject):
    """系统托盘管理器"""

    show_window = Signal()
    quit_app = Signal()
    toggle_clicker = Signal()
    show_about = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._tray = QSystemTrayIcon(self)
        self._tray.setToolTip("鼠标控制助手")

        icon = QApplication.style().standardIcon(
            QApplication.style().StandardPixmap.SP_ComputerIcon)
        self._tray.setIcon(icon)

        self._setup_menu()
        self._tray.activated.connect(self._on_activated)

    def _setup_menu(self):
        menu = QMenu()

        menu.addAction("📋 显示主窗口", self.show_window.emit)
        menu.addSeparator()

        menu.addAction("🖱️ 快速启停连点器", self.toggle_clicker.emit)
        menu.addSeparator()

        menu.addAction("ℹ️ 关于", self.show_about.emit)
        menu.addAction("❌ 退出程序", self.quit_app.emit)

        self._tray.setContextMenu(menu)

    def _on_activated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self.show_window.emit()

    def show(self):
        self._tray.show()

    def hide(self):
        self._tray.hide()

    def show_message(self, title: str, message: str,
                     icon=QSystemTrayIcon.MessageIcon.Information, duration: int = 3000):
        self._tray.showMessage(title, message, icon, duration)

    def set_icon(self, icon_path: str):
        self._tray.setIcon(QIcon(icon_path))
