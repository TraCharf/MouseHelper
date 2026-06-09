"""
自动连点器执行引擎
使用 QThread 实现不阻塞 UI 的自动点击
注意：QThread 不能重用，每次 start 需要重新创建引擎实例
"""

import pyautogui
from PySide6.QtCore import QThread, Signal, QMutex, QMutexLocker


# 配置 pyautogui（只设置一次）
pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.001

# 鼠标按钮映射
_BUTTON_MAP = {"left": "left", "right": "right", "middle": "middle"}


class ClickerEngine(QThread):
    """
    连点器引擎，运行在独立线程中。

    重要：QThread 实例只能 start() 一次。需要重新启动时，
    必须创建新的 ClickerEngine 实例。调用 stop() 后本实例不可重用。
    """

    # ── 信号（跨线程安全通信） ──
    clicked = Signal(int)        # 当前点击次数
    started = Signal()           # 线程已启动
    stopped = Signal()           # 线程已停止
    finished = Signal()          # 完成（达到指定次数）

    def __init__(self, params: dict | None = None):
        """
        :param params: 参数字典，支持以下键：
            interval_ms  - 点击间隔（毫秒），默认 100
            click_mode   - 'follow' 跟随鼠标 / 'fixed' 固定坐标，默认 'follow'
            fixed_x      - 固定坐标 X，默认 0
            fixed_y      - 固定坐标 Y，默认 0
            mouse_button - 'left' / 'right' / 'middle'，默认 'left'
            click_count  - 点击次数，0 = 无限，默认 0
            click_type   - 'single' / 'double'，默认 'single'
        """
        super().__init__()
        self._running = False
        self._paused = False
        self._total_clicks = 0
        self._mutex = QMutex()

        # 从参数加载或使用默认值
        p = params or {}
        self.interval_ms = p.get("interval_ms", 100)
        self.click_mode = p.get("click_mode", "follow")
        self.fixed_x = p.get("fixed_x", 0)
        self.fixed_y = p.get("fixed_y", 0)
        self.mouse_button = p.get("mouse_button", "left")
        self.click_count = p.get("click_count", 0)
        self.click_type = p.get("click_type", "single")

    def run(self):
        """线程主循环（不要在外部直接调用，使用 start()）"""
        self._running = True
        self._total_clicks = 0
        self.started.emit()

        while self._running:
            # 暂停检查
            if self._paused:
                self.msleep(50)
                continue

            # 执行点击
            self._do_click()
            self._total_clicks += 1
            self.clicked.emit(self._total_clicks)

            # 检查次数限制
            if self.click_count > 0 and self._total_clicks >= self.click_count:
                break

            # 间隔等待
            if self.interval_ms > 0:
                self.msleep(self.interval_ms)

        self._running = False
        self.finished.emit()
        self.stopped.emit()

    def _do_click(self):
        """执行一次点击，使用 pyautogui 统一坐标系统"""
        button = _BUTTON_MAP.get(self.mouse_button, "left")

        if self.click_mode == "fixed":
            original_pos = pyautogui.position()
            try:
                pyautogui.moveTo(self.fixed_x, self.fixed_y)
                self._click_impl(button)
            finally:
                pyautogui.moveTo(original_pos)
        else:
            self._click_impl(button)

    def _click_impl(self, button: str):
        """实际的点击操作"""
        if self.click_type == "double":
            pyautogui.doubleClick(button=button)
        else:
            pyautogui.click(button=button)

    # ── 控制方法（线程安全） ──

    def stop(self):
        """停止并等待线程结束（阻塞调用）"""
        self._running = False
        self._paused = False
        if self.isRunning():
            self.wait(3000)  # 最多等待3秒
            if self.isRunning():
                self.terminate()  # 强制终止

    def pause(self):
        """暂停"""
        self._paused = True

    def resume(self):
        """恢复"""
        self._paused = False

    # ── 状态属性 ──

    @property
    def is_clicking(self) -> bool:
        return self._running and not self._paused

    @property
    def is_paused(self) -> bool:
        return self._paused

    @property
    def total_clicks(self) -> int:
        return self._total_clicks
