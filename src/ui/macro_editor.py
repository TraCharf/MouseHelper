"""
鼠标宏编辑器页面
可视化编辑鼠标动作序列
"""

import copy
import json
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QLabel,
    QPushButton, QListWidget, QListWidgetItem, QSpinBox,
    QDoubleSpinBox, QComboBox, QLineEdit, QFileDialog, QMessageBox,
    QGridLayout,
)

from src.core.macro_engine import MacroEngine, ACTION_TYPES
from src.data.macro_store import macro_store


ACTION_LABELS = {
    "move": "移动鼠标",
    "click": "点击",
    "wait": "等待",
    "loop_start": "循环开始",
    "loop_end": "循环结束",
    "key_press": "按键",
}


class MacroEditorPage(QWidget):
    """鼠标宏编辑器页面"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._actions: list[dict] = []
        self._engine: MacroEngine | None = None
        self._current_edit_index = -1
        self._prop_widgets: dict = {}

        self._setup_ui()
        self._connect_signals()

    # ═══════════════════════════════════════════
    # UI 构建
    # ═══════════════════════════════════════════

    def _setup_ui(self):
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(20, 16, 20, 16)
        main_layout.setSpacing(12)

        # ── 左侧面板 ──
        left_panel = QVBoxLayout()
        left_panel.setSpacing(8)

        title = QLabel("鼠标宏编辑器")
        title.setObjectName("titleLabel")
        left_panel.addWidget(title)

        # 添加动作
        add_group = QGroupBox("添加动作")
        add_layout = QVBoxLayout(add_group)
        btn_grid = QGridLayout()
        btn_specs = [
            ("🖱️ 移动", "move", 0, 0),
            ("👆 点击", "click", 0, 1),
            ("⏱️ 等待", "wait", 1, 0),
            ("🔁 循环开始", "loop_start", 1, 1),
            ("🔁 循环结束", "loop_end", 2, 0),
            ("⌨️ 按键", "key_press", 2, 1),
        ]
        for label, atype, r, c in btn_specs:
            btn = QPushButton(label)
            btn.clicked.connect(lambda checked, t=atype: self._add_action(t))
            btn.setToolTip(f"添加{ACTION_LABELS[atype]}动作")
            btn_grid.addWidget(btn, r, c)
        add_layout.addLayout(btn_grid)
        left_panel.addWidget(add_group)

        # 动作列表
        list_group = QGroupBox("动作序列")
        list_layout = QVBoxLayout(list_group)
        self._action_list = QListWidget()
        self._action_list.currentRowChanged.connect(self._on_selection_changed)
        list_layout.addWidget(self._action_list)

        op_layout = QHBoxLayout()
        for text, slot in [("↑ 上移", self._move_up),
                           ("↓ 下移", self._move_down),
                           ("🗑️ 删除", self._delete_action),
                           ("📋 复制", self._duplicate_action)]:
            btn = QPushButton(text)
            btn.clicked.connect(slot)
            op_layout.addWidget(btn)
        list_layout.addLayout(op_layout)
        left_panel.addWidget(list_group)

        # 执行 & 文件
        exec_layout = QHBoxLayout()
        self._run_btn = QPushButton("▶ 执行宏")
        self._run_btn.setObjectName("primaryBtn")
        self._run_btn.clicked.connect(self._toggle_execute)
        exec_layout.addWidget(self._run_btn)
        exec_layout.addWidget(QLabel("整体循环:"))
        self._macro_loop = QSpinBox()
        self._macro_loop.setRange(1, 999)
        self._macro_loop.setValue(1)
        exec_layout.addWidget(self._macro_loop)
        self._save_macro_btn = QPushButton("💾 保存")
        self._save_macro_btn.clicked.connect(self._save_macro)
        exec_layout.addWidget(self._save_macro_btn)
        self._load_macro_btn = QPushButton("📂 加载")
        self._load_macro_btn.clicked.connect(self._load_macro)
        exec_layout.addWidget(self._load_macro_btn)
        left_panel.addLayout(exec_layout)

        self._exec_status = QLabel("")
        left_panel.addWidget(self._exec_status)

        main_layout.addLayout(left_panel, 2)

        # ── 右侧属性面板 ──
        right_panel = QVBoxLayout()
        prop_group = QGroupBox("动作属性")
        self._prop_layout = QVBoxLayout(prop_group)
        self._prop_stack = QVBoxLayout()
        self._prop_layout.addLayout(self._prop_stack)
        self._prop_layout.addStretch()
        right_panel.addWidget(prop_group)

        self._apply_btn = QPushButton("✅ 应用修改")
        self._apply_btn.clicked.connect(self._apply_changes)
        self._apply_btn.setEnabled(False)
        right_panel.addWidget(self._apply_btn)
        right_panel.addStretch()
        main_layout.addLayout(right_panel, 3)

    def _connect_signals(self):
        pass  # 引擎信号在 _start_engine 中动态连接

    # ═══════════════════════════════════════════
    # 动作管理
    # ═══════════════════════════════════════════

    def _add_action(self, atype: str):
        defaults = {
            "move": {"type": "move", "mode": "absolute", "x": 0, "y": 0, "duration": 0},
            "click": {"type": "click", "button": "left", "click_type": "single"},
            "wait": {"type": "wait", "duration": 1000},
            "loop_start": {"type": "loop_start", "count": 3},
            "loop_end": {"type": "loop_end"},
            "key_press": {"type": "key_press", "key": "enter"},
        }
        self._actions.append(defaults.get(atype, {"type": atype}))
        self._refresh_list()
        self._action_list.setCurrentRow(len(self._actions) - 1)

    def _refresh_list(self):
        self._action_list.clear()
        for i, action in enumerate(self._actions):
            text = self._format_action(i, action)
            item = QListWidgetItem(text)
            item.setData(Qt.ItemDataRole.UserRole, i)
            self._action_list.addItem(item)

    def _format_action(self, index: int, action: dict) -> str:
        atype = action.get("type", "?")
        base = ACTION_LABELS.get(atype, atype)
        if atype == "move":
            mode = "相对" if action.get("mode") == "relative" else "绝对"
            base += f" [{mode}] → ({action.get('x', 0)}, {action.get('y', 0)})"
        elif atype == "click":
            btn_map = {"left": "左键", "right": "右键", "middle": "中键"}
            base += f" {btn_map.get(action.get('button', 'left'), '左键')}"
        elif atype == "wait":
            base += f" {action.get('duration', 1000)}ms"
        elif atype == "loop_start":
            base += f" ×{action.get('count', 3)}"
        elif atype == "key_press":
            base += f" [{action.get('key', '?')}]"
        return f"#{index + 1} {base}"

    def _move_up(self):
        row = self._action_list.currentRow()
        if row > 0:
            self._actions[row], self._actions[row - 1] = \
                self._actions[row - 1], self._actions[row]
            self._refresh_list()
            self._action_list.setCurrentRow(row - 1)

    def _move_down(self):
        row = self._action_list.currentRow()
        if row < len(self._actions) - 1:
            self._actions[row], self._actions[row + 1] = \
                self._actions[row + 1], self._actions[row]
            self._refresh_list()
            self._action_list.setCurrentRow(row + 1)

    def _delete_action(self):
        row = self._action_list.currentRow()
        if 0 <= row < len(self._actions):
            del self._actions[row]
            self._clear_props()
            self._refresh_list()

    def _duplicate_action(self):
        row = self._action_list.currentRow()
        if 0 <= row < len(self._actions):
            self._actions.insert(row + 1, copy.deepcopy(self._actions[row]))
            self._refresh_list()
            self._action_list.setCurrentRow(row + 1)

    # ═══════════════════════════════════════════
    # 属性编辑器
    # ═══════════════════════════════════════════

    def _on_selection_changed(self, row: int):
        if row < 0 or row >= len(self._actions):
            self._clear_props()
            return
        self._current_edit_index = row
        self._build_property_editor(self._actions[row])
        self._apply_btn.setEnabled(True)

    def _clear_props(self):
        while self._prop_stack.count():
            item = self._prop_stack.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()
            elif item.layout():
                self._clear_layout(item.layout())
        self._current_edit_index = -1
        self._apply_btn.setEnabled(False)
        self._prop_widgets.clear()

    def _clear_layout(self, layout):
        while layout.count():
            item = layout.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()
            elif item.layout():
                self._clear_layout(item.layout())

    def _build_property_editor(self, action: dict):
        self._clear_props()
        self._prop_widgets = {}
        atype = action.get("type", "")

        type_label = QLabel(f"动作类型: {ACTION_LABELS.get(atype, atype)}")
        type_label.setStyleSheet("font-weight: bold; color: #e94560;")
        self._prop_stack.addWidget(type_label)

        if atype == "move":
            self._add_prop_combo("mode", "移动模式",
                                 ["absolute", "relative"], ["绝对坐标", "相对坐标"], action)
            self._add_prop_spin("x", "X 坐标", -99999, 99999, action)
            self._add_prop_spin("y", "Y 坐标", -99999, 99999, action)
            self._add_prop_spin_d("duration", "移动耗时 (秒)", 0, 10, action, 0.1)
        elif atype == "click":
            self._add_prop_combo("button", "鼠标按键",
                                 ["left", "right", "middle"], ["左键", "右键", "中键"], action)
            self._add_prop_combo("click_type", "点击类型",
                                 ["single", "double"], ["单击", "双击"], action)
        elif atype == "wait":
            self._add_prop_spin("duration", "等待时长 (毫秒)", 1, 3600000, action)
        elif atype == "loop_start":
            self._add_prop_spin("count", "循环次数", 1, 99999, action)
        elif atype == "key_press":
            self._add_prop_line("key", "按键名称", action)

    def _add_prop_combo(self, key, label, values, labels, data):
        layout = QHBoxLayout()
        layout.addWidget(QLabel(f"{label}:"))
        combo = QComboBox()
        for val, lbl in zip(values, labels):
            combo.addItem(lbl, val)
        current = data.get(key, values[0])
        idx = values.index(current) if current in values else 0
        combo.setCurrentIndex(idx)
        layout.addWidget(combo)
        layout.addStretch()
        self._prop_stack.addLayout(layout)
        self._prop_widgets[key] = combo

    def _add_prop_spin(self, key, label, min_val, max_val, data):
        layout = QHBoxLayout()
        layout.addWidget(QLabel(f"{label}:"))
        spin = QSpinBox()
        spin.setRange(min_val, max_val)
        spin.setValue(data.get(key, 0))
        layout.addWidget(spin)
        layout.addStretch()
        self._prop_stack.addLayout(layout)
        self._prop_widgets[key] = spin

    def _add_prop_spin_d(self, key, label, min_val, max_val, data, step=1.0):
        layout = QHBoxLayout()
        layout.addWidget(QLabel(f"{label}:"))
        spin = QDoubleSpinBox()
        spin.setRange(min_val, max_val)
        spin.setValue(data.get(key, 0))
        spin.setSingleStep(step)
        layout.addWidget(spin)
        layout.addStretch()
        self._prop_stack.addLayout(layout)
        self._prop_widgets[key] = spin

    def _add_prop_line(self, key, label, data):
        layout = QHBoxLayout()
        layout.addWidget(QLabel(f"{label}:"))
        line = QLineEdit(data.get(key, ""))
        layout.addWidget(line)
        layout.addStretch()
        self._prop_stack.addLayout(layout)
        self._prop_widgets[key] = line

    def _apply_changes(self):
        if self._current_edit_index < 0 or self._current_edit_index >= len(self._actions):
            return
        action = self._actions[self._current_edit_index]
        for key, widget in self._prop_widgets.items():
            if isinstance(widget, QComboBox):
                action[key] = widget.currentData()
            elif isinstance(widget, (QSpinBox, QDoubleSpinBox)):
                action[key] = widget.value()
            elif isinstance(widget, QLineEdit):
                action[key] = widget.text()
        self._refresh_list()

    # ═══════════════════════════════════════════
    # 执行
    # ═══════════════════════════════════════════

    def _toggle_execute(self):
        if self._engine and self._engine.isRunning():
            self._engine.stop()
            self._engine = None
        else:
            if not self._actions:
                QMessageBox.warning(self, "无动作", "请先添加宏动作")
                return
            # QThread 不可重用，每次创建新实例
            self._engine = MacroEngine(
                actions=copy.deepcopy(self._actions),
                loop_count=self._macro_loop.value(),
            )
            self._engine.started.connect(lambda: self._exec_status.setText("🟢 宏执行中..."))
            self._engine.stopped.connect(lambda: self._exec_status.setText("⏸️ 执行完毕"))
            self._engine.error.connect(lambda e: QMessageBox.critical(self, "执行错误", e))
            self._engine.start()

    # ═══════════════════════════════════════════
    # 文件操作
    # ═══════════════════════════════════════════

    def _save_macro(self):
        if not self._actions:
            QMessageBox.warning(self, "无动作", "请先添加宏动作")
            return
        name = f"宏_{len(macro_store.list_macros()) + 1}"
        macro_store.save_macro(name, copy.deepcopy(self._actions),
                               f"{len(self._actions)} 个动作")
        QMessageBox.information(self, "保存成功", f"宏已保存为: {name}")

    def _load_macro(self):
        filepath, _ = QFileDialog.getOpenFileName(
            self, "加载宏文件",
            str(macro_store.macros_dir) if macro_store.macros_dir.exists()
            else str(Path.home() / "Desktop"),
            "宏文件 (*.mmacro);;所有文件 (*.*)")
        if filepath:
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self._actions = data.get("actions", [])
                self._clear_props()
                self._refresh_list()
            except Exception as e:
                QMessageBox.critical(self, "加载失败", str(e))

    # ═══════════════════════════════════════════
    # 预设/配置
    # ═══════════════════════════════════════════

    def get_params(self) -> dict:
        return {"macro": {"actions": copy.deepcopy(self._actions),
                          "loop_count": self._macro_loop.value()}}

    def apply_params(self, params: dict):
        m = params.get("macro", params)
        if "actions" in m:
            self._actions = copy.deepcopy(m["actions"])
            self._refresh_list()
        if "loop_count" in m:
            self._macro_loop.setValue(m["loop_count"])

    def cleanup(self):
        if self._engine:
            self._engine.stop()
            self._engine = None
