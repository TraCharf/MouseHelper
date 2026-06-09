"""
鼠标控制助手 - 主程序入口
一款功能齐全、适合小白使用的 Windows 鼠标控制工具
"""

import os
import sys
from pathlib import Path


def _setup_dpi_awareness():
    """在导入 Qt 之前设置 DPI 感知"""
    if sys.platform != "win32":
        return
    try:
        import ctypes
        # Windows 10 1703+: 使用 SetProcessDpiAwarenessContext（推荐）
        # DPI_AWARENESS_CONTEXT_PER_MONITOR_AWARE_V2 = -4
        awareness_context = ctypes.c_long(-4)
        result = ctypes.windll.user32.SetProcessDpiAwarenessContext(awareness_context)
        if result == 0:
            # 回退：Windows 8.1 的 SetProcessDpiAwareness
            ctypes.windll.shcore.SetProcessDpiAwareness(2)
    except Exception:
        try:
            import ctypes
            # 最终回退：Windows Vista/7 的 SetProcessDPIAware
            ctypes.windll.user32.SetProcessDPIAware()
        except Exception:
            pass


# 必须在导入 PySide6 之前设置 DPI 感知（避免重复设置导致警告）
_setup_dpi_awareness()

# 抑制 Qt DPI 重复设置的警告（我们已经手动设置过了）
os.environ["QT_LOGGING_RULES"] = "qt.qpa.window=false"

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt

from src.ui.main_window import MainWindow


def _get_base_path() -> Path:
    """获取资源根目录（兼容 PyInstaller 打包）"""
    if hasattr(sys, '_MEIPASS'):
        # PyInstaller 打包后的临时目录
        return Path(sys._MEIPASS)
    return Path(__file__).parent


def load_stylesheet() -> str:
    """加载 QSS 样式表"""
    style_path = _get_base_path() / "resources" / "style.qss"
    if style_path.exists():
        with open(style_path, "r", encoding="utf-8") as f:
            return f.read()
    return ""


def is_admin() -> bool:
    """检查是否以管理员权限运行"""
    try:
        import ctypes
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except Exception:
        return False


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("鼠标控制助手")
    app.setOrganizationName("MouseHelper")
    app.setApplicationVersion("1.0.0")

    # 加载样式表
    stylesheet = load_stylesheet()
    if stylesheet:
        app.setStyleSheet(stylesheet)

    # 检查管理员权限（全局热键需要）
    if not is_admin():
        from PySide6.QtWidgets import QMessageBox
        QMessageBox.warning(
            None, "权限提示",
            "⚠️ 检测到程序未以管理员身份运行。\n\n"
            "全局热键功能（F6/F7/F8 快捷键）可能无法正常工作。\n\n"
            "建议：右键点击程序 → 以管理员身份运行",
        )

    # 创建主窗口
    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
