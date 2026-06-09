"""
回放引擎
按照事件序列回放录制的鼠标操作
注意：QThread 不可重用，每次回放需创建新实例
"""

import json

import pyautogui
from PySide6.QtCore import QThread, Signal


pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.001


class PlayerEngine(QThread):
    """
    回放引擎，运行在独立线程中。

    重要：QThread 实例只能 start() 一次。停止后必须创建新实例。
    """

    progress = Signal(int, int)   # (current_event, total_events)
    started = Signal()
    stopped = Signal()
    finished = Signal()

    def __init__(self, events: list[dict] | None = None, speed: float = 1.0,
                 loop_count: int = 1):
        """
        :param events: 事件列表（录制数据）
        :param speed: 回放速度倍率 (0.1 ~ 10.0)
        :param loop_count: 循环次数（0 = 无限）
        """
        super().__init__()
        self._events = events or []
        self._speed = max(0.1, min(10.0, speed))
        self._loop_count = loop_count
        self._running = False
        self._current_event = 0
        self._current_loop = 0

    # ── 参数设置 ──

    def set_events(self, events: list[dict]):
        self._events = events

    def set_speed(self, speed: float):
        self._speed = max(0.1, min(10.0, speed))

    def set_loop_count(self, count: int):
        self._loop_count = count

    @classmethod
    def load_from_file(cls, filepath: str) -> "PlayerEngine":
        """从录制文件创建引擎"""
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        return cls(events=data.get("events", []))

    # ── 线程主循环 ──

    def run(self):
        self._running = True
        self._current_loop = 0
        self.started.emit()

        while self._running:
            if self._loop_count > 0 and self._current_loop >= self._loop_count:
                break
            self._current_loop += 1
            self._play_once()

        self._running = False
        self.finished.emit()
        self.stopped.emit()

    def _play_once(self):
        if not self._events:
            return
        total = len(self._events)
        prev_time = 0.0

        for i, event in enumerate(self._events):
            if not self._running:
                break

            self._current_event = i + 1
            self.progress.emit(self._current_event, total)

            # 计算延迟（考虑速度倍率）
            current_time = event.get("timestamp", 0.0)
            delay = (current_time - prev_time) / self._speed
            if delay > 0:
                self.msleep(int(delay * 1000))

            if not self._running:
                break

            self._execute_event(event)
            prev_time = current_time

    def _execute_event(self, event: dict):
        etype = event.get("type")

        if etype == "move":
            pyautogui.moveTo(event["x"], event["y"])
        elif etype == "click":
            btn = event.get("button", "left")
            if event.get("pressed"):
                pyautogui.mouseDown(event["x"], event["y"], button=btn)
            else:
                pyautogui.mouseUp(event["x"], event["y"], button=btn)
        elif etype == "scroll":
            pyautogui.scroll(event.get("dy", 0))

    # ── 控制 ──

    def stop(self):
        self._running = False
        if self.isRunning():
            self.wait(3000)
            if self.isRunning():
                self.terminate()

    @property
    def is_playing(self) -> bool:
        return self._running

    @property
    def event_count(self) -> int:
        return len(self._events)
