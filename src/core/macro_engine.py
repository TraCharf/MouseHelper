"""
鼠标宏执行引擎
解析动作序列并执行，支持循环嵌套
注意：QThread 不可重用，每次执行需创建新实例
"""

import pyautogui
from PySide6.QtCore import QThread, Signal


pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.001

ACTION_TYPES = ("move", "click", "wait", "loop_start", "loop_end", "key_press")


class MacroEngine(QThread):
    """宏执行引擎（独立线程）"""

    progress = Signal(int, int)   # (current_index, total_actions)
    started = Signal()
    stopped = Signal()
    finished = Signal()
    error = Signal(str)

    def __init__(self, actions: list[dict] | None = None, loop_count: int = 1):
        """
        :param actions: 动作列表
        :param loop_count: 整体循环次数
        """
        super().__init__()
        self._actions = actions or []
        self._loop_count = loop_count
        self._running = False

    def set_actions(self, actions: list[dict]):
        self._actions = actions

    def set_loop_count(self, count: int):
        self._loop_count = count

    # ── 线程主循环 ──

    def run(self):
        self._running = True
        self.started.emit()
        try:
            for _ in range(max(1, self._loop_count)):
                if not self._running:
                    break
                self._execute_actions(self._actions, 0)
        except Exception as e:
            self.error.emit(str(e))
        finally:
            self._running = False
            self.finished.emit()
            self.stopped.emit()

    def _execute_actions(self, actions: list[dict], depth: int) -> int:
        """递归执行动作列表，返回下一个要执行的索引"""
        i = 0
        n = len(actions)
        while i < n and self._running:
            action = actions[i]
            atype = action.get("type", "")
            total = len(self._actions)
            self.progress.emit(i + 1, total)

            if atype == "move":
                self._do_move(action)
            elif atype == "click":
                self._do_click(action)
            elif atype == "wait":
                self._do_wait(action)
            elif atype == "key_press":
                self._do_key_press(action)
            elif atype == "loop_start":
                count = action.get("count", 1)
                body, end = self._collect_loop_body(actions, i + 1)
                for _ in range(count):
                    if not self._running:
                        break
                    self._execute_actions(body, depth + 1)
                i = end
            elif atype == "loop_end":
                pass  # 仅作为标记，由 _collect_loop_body 处理

            i += 1
        return i

    # ── 动作执行 ──

    def _do_move(self, action: dict):
        mode = action.get("mode", "absolute")
        duration = action.get("duration", 0)
        if mode == "relative":
            pyautogui.moveRel(
                action.get("dx", 0), action.get("dy", 0),
                duration=duration,
            )
        else:
            pyautogui.moveTo(
                action.get("x", 0), action.get("y", 0),
                duration=duration,
            )

    def _do_click(self, action: dict):
        button = action.get("button", "left")
        click_type = action.get("click_type", "single")
        if click_type == "double":
            pyautogui.doubleClick(button=button)
        elif click_type == "right":
            pyautogui.rightClick()
        else:
            pyautogui.click(button=button)

    def _do_wait(self, action: dict):
        duration = action.get("duration", 100)
        if duration > 0:
            self.msleep(duration)

    def _do_key_press(self, action: dict):
        key = action.get("key", "")
        if key:
            pyautogui.press(key)

    # ── 循环体解析 ──

    @staticmethod
    def _collect_loop_body(actions: list[dict], start: int) -> tuple[list[dict], int]:
        """收集匹配的 loop_start 和 loop_end 之间的动作"""
        depth = 0
        body: list[dict] = []
        for i in range(start, len(actions)):
            t = actions[i].get("type", "")
            if t == "loop_start":
                depth += 1
            elif t == "loop_end":
                if depth == 0:
                    return body, i
                depth -= 1
            body.append(actions[i])
        return body, len(actions)

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
