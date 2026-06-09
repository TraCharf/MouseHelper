"""
全局热键引擎
基于 pynput.keyboard 实现，在独立线程中监听按键
通过 Qt Signal 将回调安全地投递到主线程
"""

import threading
from collections.abc import Callable

from pynput import keyboard
from PySide6.QtCore import QObject, Signal


class HotkeyEngine(QObject):
    """
    全局热键管理器

    特性：
    - 基于 pynput.keyboard.Listener，在独立线程运行
    - 支持组合键（如 ctrl+shift+a）
    - 通过 Signal 将回调安全投递到 Qt 主线程
    - 500ms 防抖，避免重复触发
    """

    triggered = Signal(str)  # 发射 action_name，由外部统一连接

    def __init__(self):
        super().__init__()
        self._callbacks: dict[str, Callable] = {}
        self._hotkey_map: dict[str, str] = {}
        self._lock = threading.RLock()
        self._listener: keyboard.Listener | None = None
        self._pressed_keys: set[str] = set()
        self._started = False
        self._start_lock = threading.Lock()
        self._last_triggered: dict[str, float] = {}

        # 内部连接：signal → 执行对应 callback
        self.triggered.connect(self._dispatch)

    # ── 公共接口 ──

    def register(self, action_name: str, hotkey: str, callback: Callable):
        with self._lock:
            self.unregister(action_name)
            normalized = self._normalize_key(hotkey)
            self._callbacks[action_name] = callback
            self._hotkey_map[action_name] = normalized
        self._ensure_listener()

    def unregister(self, action_name: str):
        with self._lock:
            self._callbacks.pop(action_name, None)
            self._hotkey_map.pop(action_name, None)
            self._last_triggered.pop(action_name, None)

    def unregister_all(self):
        with self._lock:
            self._callbacks.clear()
            self._hotkey_map.clear()
            self._last_triggered.clear()
        if self._listener:
            self._listener.stop()
            self._started = False
            self._listener = None

    def is_registered(self, action_name: str) -> bool:
        return action_name in self._callbacks

    # ── 信号分发 ──

    def _dispatch(self, action_name: str):
        """在主线程中执行回调"""
        callback = self._callbacks.get(action_name)
        if callback:
            try:
                callback()
            except Exception:
                pass

    # ── 内部 ──

    def _ensure_listener(self):
        if self._started:
            return
        with self._start_lock:
            if self._started:
                return
            self._listener = keyboard.Listener(
                on_press=self._on_press,
                on_release=self._on_release,
            )
            self._listener.daemon = True
            self._listener.start()
            self._started = True

    def _on_press(self, key):
        name = self._key_to_name(key)
        if name:
            self._pressed_keys.add(name)
        self._check_hotkeys()

    def _on_release(self, key):
        name = self._key_to_name(key)
        if name:
            self._pressed_keys.discard(name)

    def _check_hotkeys(self):
        if not self._pressed_keys:
            return
        import time
        now = time.monotonic()
        pressed = frozenset(self._pressed_keys)

        with self._lock:
            for action_name, hotkey_str in list(self._hotkey_map.items()):
                required = self._parse_combo(hotkey_str)
                if not required or not required.issubset(pressed):
                    continue
                if now - self._last_triggered.get(action_name, 0) < 0.5:
                    continue
                self._last_triggered[action_name] = now
                # 从 pynput 线程发射信号 → Qt 自动排队到主线程
                self.triggered.emit(action_name)

    # ── 静态工具 ──

    @staticmethod
    def _key_to_name(key) -> str | None:
        try:
            if hasattr(key, 'char') and key.char:
                return key.char.lower()
        except Exception:
            pass
        try:
            if hasattr(key, 'name') and key.name:
                return key.name.lower()
        except Exception:
            pass
        return None

    @staticmethod
    def _normalize_key(hotkey: str) -> str:
        return hotkey.lower().strip()

    @staticmethod
    def _parse_combo(hotkey: str) -> set[str] | None:
        if not hotkey:
            return None
        return {p.strip() for p in hotkey.split('+')}


# 全局单例
hotkey_engine = HotkeyEngine()
