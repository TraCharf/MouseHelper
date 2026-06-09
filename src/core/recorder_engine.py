"""
鼠标录制引擎
使用 pynput 监听鼠标事件并记录为动作序列
"""

import time
import threading
from typing import Any, Callable

from pynput import mouse


class RecorderEngine:
    """鼠标录制引擎（基于 pynput.mouse.Listener）"""

    def __init__(self):
        self._recording = False
        self._events: list[dict[str, Any]] = []
        self._listener: mouse.Listener | None = None
        self._start_time = 0.0
        self._lock = threading.RLock()
        self._event_callback: Callable[[dict], None] | None = None

    # ── 公共接口 ──

    def set_event_callback(self, callback: Callable[[dict], None] | None):
        """设置事件回调（注意：回调在 pynput 线程中执行，需要自行处理线程安全）"""
        self._event_callback = callback

    def start(self) -> bool:
        """开始录制。已录制时返回 False"""
        if self._recording:
            return False
        with self._lock:
            self._events.clear()
            self._recording = True
            self._start_time = time.perf_counter()

        self._listener = mouse.Listener(
            on_move=self._on_move,
            on_click=self._on_click,
            on_scroll=self._on_scroll,
        )
        self._listener.start()
        return True

    def stop(self) -> list[dict[str, Any]]:
        """停止录制并返回录制的事件列表（拷贝）"""
        with self._lock:
            self._recording = False

        if self._listener:
            self._listener.stop()
            self._listener = None

        with self._lock:
            return list(self._events)

    @property
    def is_recording(self) -> bool:
        return self._recording

    @property
    def event_count(self) -> int:
        with self._lock:
            return len(self._events)

    @property
    def duration(self) -> float:
        with self._lock:
            if not self._events:
                return 0.0
            return self._events[-1].get("timestamp", 0.0)

    def export_data(self) -> dict[str, Any]:
        """导出录制数据为可序列化的字典"""
        with self._lock:
            return {
                "version": "1.0",
                "duration": self.duration,
                "event_count": len(self._events),
                "events": list(self._events),
            }

    # ── 内部方法 ──

    def _add_event(self, event: dict):
        """线程安全地添加事件"""
        if not self._recording:
            return
        with self._lock:
            event["timestamp"] = round(time.perf_counter() - self._start_time, 4)
            self._events.append(event)
        # 回调在锁外执行，避免死锁
        cb = self._event_callback
        if cb:
            try:
                cb(event)
            except Exception:
                pass

    def _on_move(self, x: int, y: int):
        self._add_event({"type": "move", "x": x, "y": y})

    def _on_click(self, x: int, y: int, button, pressed: bool):
        btn_name = getattr(button, "name", str(button))
        self._add_event({
            "type": "click",
            "x": x, "y": y,
            "button": btn_name,
            "pressed": pressed,
        })

    def _on_scroll(self, x: int, y: int, dx: int, dy: int):
        self._add_event({
            "type": "scroll",
            "x": x, "y": y,
            "dx": dx, "dy": dy,
        })
