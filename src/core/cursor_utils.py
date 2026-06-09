"""
光标工具模块
提供坐标跟踪、颜色拾取、光标高亮等功能
"""

from PySide6.QtCore import QTimer, QObject, Signal
from PySide6.QtGui import QCursor
from PySide6.QtWidgets import QApplication
import pyautogui
from pynput import mouse


class CursorTracker(QObject):
    """实时追踪光标位置和像素颜色（基于 QTimer）"""

    position_changed = Signal(int, int)
    color_changed = Signal(int, int, int)

    def __init__(self, interval_ms: int = 50, parent=None):
        super().__init__(parent)
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._poll)
        self._interval = interval_ms
        self._active = False

    def start(self):
        self._active = True
        self._timer.start(self._interval)

    def stop(self):
        self._active = False
        self._timer.stop()

    @property
    def is_active(self) -> bool:
        return self._active

    def _poll(self):
        if not self._active:
            return
        pos = QCursor.pos()
        x, y = pos.x(), pos.y()
        self.position_changed.emit(x, y)

        try:
            pixel = pyautogui.pixel(x, y)
            self.color_changed.emit(pixel[0], pixel[1], pixel[2])
        except (OSError, Exception):
            pass


class CursorHighlighter:
    """光标高亮效果（使用 tkinter 透明覆盖窗口绘制圆圈）"""

    def __init__(self):
        self._active = False
        self._radius = 30
        self._color = (255, 80, 80)
        self._line_width = 2
        self._overlay = None

    def start(self, radius: int = 30, color: tuple = (255, 80, 80)):
        self._radius = radius
        self._color = color
        self._active = True
        self._start_overlay()

    def stop(self):
        self._active = False
        if self._overlay:
            try:
                self._overlay.destroy()
            except Exception:
                pass
            self._overlay = None

    @property
    def is_active(self) -> bool:
        return self._active

    def _start_overlay(self):
        import tkinter as tk

        root = tk.Tk()
        root.title("CursorHighlighter")
        root.attributes("-topmost", True)
        root.attributes("-transparentcolor", "black")
        root.overrideredirect(True)
        root.geometry(f"{self._radius * 3}x{self._radius * 3}+0+0")

        canvas = tk.Canvas(root, bg="black", highlightthickness=0)
        canvas.pack(fill="both", expand=True)

        def _update():
            if not self._active:
                root.destroy()
                return
            try:
                x, y = root.winfo_pointerxy()
                r = self._radius
                root.geometry(f"{r * 3}x{r * 3}+{int(x - r * 1.5)}+{int(y - r * 1.5)}")
                canvas.delete("all")
                hex_color = f"#{self._color[0]:02x}{self._color[1]:02x}{self._color[2]:02x}"
                canvas.create_oval(2, 2, r * 3, r * 3, outline=hex_color, width=self._line_width)
                root.after(16, _update)
            except Exception:
                pass

        root.after(16, _update)
        self._overlay = root


# ── 工具函数 ──

def get_cursor_pos() -> tuple[int, int]:
    """获取当前鼠标位置（使用 pyautogui 保证与点击引擎坐标一致）"""
    pos = pyautogui.position()
    return pos.x, pos.y


def get_pixel_color(x: int | None = None, y: int | None = None) -> tuple[int, int, int]:
    """获取指定位置或当前位置的像素 RGB 颜色"""
    if x is None or y is None:
        x, y = get_cursor_pos()
    try:
        pixel = pyautogui.pixel(x, y)
        return pixel[0], pixel[1], pixel[2]
    except Exception:
        return 0, 0, 0


def rgb_to_hex(r: int, g: int, b: int) -> str:
    """RGB 转 HEX 字符串"""
    return f"#{r:02X}{g:02X}{b:02X}"
