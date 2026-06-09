"""
自动连点器页面
"""

import pyautogui
from PySide6.QtCore import Qt, QTimer, Signal, QObject
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QLabel,
    QSpinBox, QComboBox, QRadioButton, QPushButton, QButtonGroup,
    QGridLayout, QFrame,
)

from src.core.clicker_engine import ClickerEngine
from src.core.hotkey_engine import hotkey_engine
from src.data.config import config


# 按钮状态样式类名映射
_STYLE_STOPPED = ("primaryBtn", "statusStopped")
_STYLE_RUNNING = ("dangerBtn", "statusRunning")


class AutoClickerPage(QWidget):
    """自动连点器页面"""

    # 坐标拾取完成信号（线程安全）
    _pick_done = Signal(int, int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._engine: ClickerEngine | None = None
        self._pick_timer: QTimer | None = None
        self._pick_countdown = 0

        self._setup_ui()
        self._connect_signals()
        self._load_settings()
        self._register_hotkey()

    # ═══════════════════════════════════════════
    # UI 构建
    # ═══════════════════════════════════════════

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 16, 20, 16)
        main_layout.setSpacing(12)

        title = QLabel("自动连点器")
        title.setObjectName("titleLabel")
        main_layout.addWidget(title)

        # ── 点击设置 ──
        settings_group = QGroupBox("点击设置")
        settings_layout = QGridLayout(settings_group)
        settings_layout.setSpacing(10)
        row = 0

        # 点击间隔
        settings_layout.addWidget(QLabel("点击间隔:"), row, 0)
        interval_layout = QHBoxLayout()
        self._interval_spin = QSpinBox()
        self._interval_spin.setRange(1, 999999)
        self._interval_spin.setValue(100)
        self._interval_spin.setSuffix(" ms")
        self._interval_spin.setToolTip("设置每次点击之间的间隔时间")
        interval_layout.addWidget(self._interval_spin)
        for label, val in [("10ms", 10), ("50ms", 50), ("100ms", 100),
                           ("500ms", 500), ("1s", 1000)]:
            btn = QPushButton(label)
            btn.setFixedWidth(48)
            btn.clicked.connect(lambda checked, v=val: self._interval_spin.setValue(v))
            interval_layout.addWidget(btn)
        settings_layout.addLayout(interval_layout, row, 1)
        row += 1

        # 点击方式
        settings_layout.addWidget(QLabel("点击方式:"), row, 0)
        mode_layout = QHBoxLayout()
        self._mode_group = QButtonGroup(self)
        self._follow_rb = QRadioButton("跟随鼠标")
        self._fixed_rb = QRadioButton("固定坐标")
        self._mode_group.addButton(self._follow_rb, 0)
        self._mode_group.addButton(self._fixed_rb, 1)
        self._follow_rb.setChecked(True)
        mode_layout.addWidget(self._follow_rb)
        mode_layout.addWidget(self._fixed_rb)
        mode_layout.addStretch()
        settings_layout.addLayout(mode_layout, row, 1)
        row += 1

        # 固定坐标
        settings_layout.addWidget(QLabel("固定坐标:"), row, 0)
        coord_layout = QHBoxLayout()
        coord_layout.addWidget(QLabel("X:"))
        self._fixed_x = QSpinBox()
        self._fixed_x.setRange(0, 99999)
        self._fixed_x.setEnabled(False)
        coord_layout.addWidget(self._fixed_x)
        coord_layout.addWidget(QLabel("Y:"))
        self._fixed_y = QSpinBox()
        self._fixed_y.setRange(0, 99999)
        self._fixed_y.setEnabled(False)
        coord_layout.addWidget(self._fixed_y)
        self._pick_btn = QPushButton("📍 拾取位置 (3秒)")
        self._pick_btn.setToolTip("3秒倒计时后在当前鼠标位置记录坐标\n使用与点击引擎相同的坐标系统")
        self._pick_btn.clicked.connect(self._start_pick)
        self._pick_btn.setEnabled(False)
        coord_layout.addWidget(self._pick_btn)
        coord_layout.addStretch()
        settings_layout.addLayout(coord_layout, row, 1)
        row += 1

        # 鼠标按键
        settings_layout.addWidget(QLabel("鼠标按键:"), row, 0)
        btn_layout = QHBoxLayout()
        self._button_combo = QComboBox()
        self._button_combo.addItems(["左键", "右键", "中键"])
        btn_layout.addWidget(self._button_combo)
        btn_layout.addStretch()
        settings_layout.addLayout(btn_layout, row, 1)
        row += 1

        # 点击类型
        settings_layout.addWidget(QLabel("点击类型:"), row, 0)
        type_layout = QHBoxLayout()
        self._click_type_combo = QComboBox()
        self._click_type_combo.addItems(["单击", "双击"])
        type_layout.addWidget(self._click_type_combo)
        type_layout.addStretch()
        settings_layout.addLayout(type_layout, row, 1)
        row += 1

        # 点击次数
        settings_layout.addWidget(QLabel("点击次数:"), row, 0)
        count_layout = QHBoxLayout()
        self._count_mode_group = QButtonGroup(self)
        self._limited_rb = QRadioButton("指定次数")
        self._unlimited_rb = QRadioButton("无限循环")
        self._count_mode_group.addButton(self._limited_rb, 0)
        self._count_mode_group.addButton(self._unlimited_rb, 1)
        self._unlimited_rb.setChecked(True)
        count_layout.addWidget(self._limited_rb)
        self._count_spin = QSpinBox()
        self._count_spin.setRange(1, 999999)
        self._count_spin.setValue(100)
        self._count_spin.setEnabled(False)
        count_layout.addWidget(self._count_spin)
        count_layout.addWidget(QLabel("次"))
        count_layout.addWidget(self._unlimited_rb)
        count_layout.addStretch()
        settings_layout.addLayout(count_layout, row, 1)
        row += 1

        # 热键提示
        hotkey = config.get("hotkeys", "clicker_toggle", default="F6")
        settings_layout.addWidget(QLabel("快捷键:"), row, 0)
        self._hotkey_label = QLabel(f"按 [{hotkey.upper()}] 开始/停止连点")
        self._hotkey_label.setStyleSheet("color: #2ecc71; font-weight: bold;")
        settings_layout.addWidget(self._hotkey_label, row, 1)

        main_layout.addWidget(settings_group)

        # ── 控制按钮 ──
        ctrl_layout = QHBoxLayout()
        self._start_btn = QPushButton("▶ 开始连点")
        self._start_btn.setObjectName("primaryBtn")
        self._start_btn.setMinimumHeight(40)
        self._start_btn.clicked.connect(self._toggle_clicker)
        ctrl_layout.addWidget(self._start_btn)
        self._save_preset_btn = QPushButton("💾 保存为预设")
        self._save_preset_btn.clicked.connect(self._save_as_preset)
        ctrl_layout.addWidget(self._save_preset_btn)
        main_layout.addLayout(ctrl_layout)

        # ── 状态 ──
        status_frame = QFrame()
        status_frame.setFrameShape(QFrame.Shape.StyledPanel)
        status_frame.setStyleSheet(
            "QFrame { background-color: #16213e; border-radius: 6px; padding: 10px; }"
        )
        status_layout = QHBoxLayout(status_frame)
        self._status_label = QLabel("⏸️ 已停止")
        self._status_label.setObjectName("statusStopped")
        status_layout.addWidget(self._status_label)
        status_layout.addStretch()
        self._count_label = QLabel("已点击: 0 次")
        status_layout.addWidget(self._count_label)
        main_layout.addWidget(status_frame)

        main_layout.addStretch()

    # ═══════════════════════════════════════════
    # 信号连接
    # ═══════════════════════════════════════════

    def _connect_signals(self):
        self._follow_rb.toggled.connect(self._on_mode_changed)
        self._limited_rb.toggled.connect(self._on_count_mode_changed)
        self._pick_done.connect(self._on_pick_done)

    def _connect_engine_signals(self):
        if self._engine:
            self._engine.started.connect(self._on_engine_started)
            self._engine.stopped.connect(self._on_engine_stopped)
            self._engine.clicked.connect(self._on_click)

    def _disconnect_engine_signals(self):
        if self._engine:
            try:
                self._engine.started.disconnect(self._on_engine_started)
            except Exception:
                pass
            try:
                self._engine.stopped.disconnect(self._on_engine_stopped)
            except Exception:
                pass
            try:
                self._engine.clicked.disconnect(self._on_click)
            except Exception:
                pass

    # ═══════════════════════════════════════════
    # 连点器控制
    # ═══════════════════════════════════════════

    def _toggle_clicker(self):
        if self._engine and self._engine.isRunning():
            self._stop_engine()
        else:
            self._start_engine()

    def _start_engine(self):
        # QThread 不可重用，每次创建新实例
        params = self._collect_params()
        self._engine = ClickerEngine(params)
        self._connect_engine_signals()
        self._engine.start()

    def _stop_engine(self):
        if self._engine:
            self._engine.stop()
            self._disconnect_engine_signals()
            self._engine = None

    def _collect_params(self) -> dict:
        btn_map = {"左键": "left", "右键": "right", "中键": "middle"}
        return {
            "interval_ms": self._interval_spin.value(),
            "click_mode": "fixed" if self._fixed_rb.isChecked() else "follow",
            "fixed_x": self._fixed_x.value(),
            "fixed_y": self._fixed_y.value(),
            "mouse_button": btn_map.get(self._button_combo.currentText(), "left"),
            "click_type": "double" if self._click_type_combo.currentText() == "双击" else "single",
            "click_count": self._count_spin.value() if self._limited_rb.isChecked() else 0,
        }

    # ═══════════════════════════════════════════
    # 坐标拾取（使用 pyautogui 保证坐标一致）
    # ═══════════════════════════════════════════

    def _start_pick(self):
        """开始3秒倒计时拾取坐标"""
        self._pick_btn.setEnabled(False)
        self._pick_countdown = 3
        self._pick_btn.setText(f"⏳ {self._pick_countdown}秒后拾取...")

        self._pick_timer = QTimer(self)
        self._pick_timer.timeout.connect(self._pick_tick)
        self._pick_timer.start(1000)

    def _pick_tick(self):
        self._pick_countdown -= 1
        if self._pick_countdown <= 0:
            self._pick_timer.stop()
            self._pick_timer = None
            # 使用 pyautogui.position() 与点击引擎完全一致
            pos = pyautogui.position()
            self._pick_done.emit(pos.x, pos.y)
        else:
            self._pick_btn.setText(f"⏳ {self._pick_countdown}秒后拾取...")

    def _on_pick_done(self, x: int, y: int):
        """坐标拾取完成（在主线程执行）"""
        self._fixed_x.setValue(x)
        self._fixed_y.setValue(y)
        self._pick_btn.setText("📍 拾取位置 (3秒)")
        self._pick_btn.setEnabled(True)

    # ═══════════════════════════════════════════
    # 引擎信号处理
    # ═══════════════════════════════════════════

    def _on_engine_started(self):
        self._start_btn.setText("⏹ 停止连点")
        self._update_btn_style(self._start_btn, "dangerBtn")
        self._status_label.setText("🟢 运行中")
        self._update_btn_style(self._status_label, "statusRunning")

    def _on_engine_stopped(self):
        self._start_btn.setText("▶ 开始连点")
        self._update_btn_style(self._start_btn, "primaryBtn")
        self._status_label.setText("⏸️ 已停止")
        self._update_btn_style(self._status_label, "statusStopped")
        self._engine = None

    def _on_click(self, count: int):
        self._count_label.setText(f"已点击: {count} 次")

    # ═══════════════════════════════════════════
    # UI 事件
    # ═══════════════════════════════════════════

    def _on_mode_changed(self):
        is_fixed = self._fixed_rb.isChecked()
        self._fixed_x.setEnabled(is_fixed)
        self._fixed_y.setEnabled(is_fixed)
        self._pick_btn.setEnabled(is_fixed)

    def _on_count_mode_changed(self):
        self._count_spin.setEnabled(self._limited_rb.isChecked())

    def _register_hotkey(self):
        hotkey = config.get("hotkeys", "clicker_toggle", default="f6")
        hotkey_engine.register("clicker_toggle", hotkey, self._toggle_clicker)

    # ═══════════════════════════════════════════
    # 预设/配置
    # ═══════════════════════════════════════════

    def _save_as_preset(self):
        from src.data.preset_store import preset_store
        params = {"clicker": self._collect_params()}
        preset_store.save_preset("连点器预设", params, "从连点器页面保存")

    def _load_settings(self):
        self._interval_spin.setValue(config.get("clicker", "interval_ms", default=100))
        mode = config.get("clicker", "click_mode", default="follow")
        if mode == "fixed":
            self._fixed_rb.setChecked(True)
        self._fixed_x.setValue(config.get("clicker", "fixed_x", default=0))
        self._fixed_y.setValue(config.get("clicker", "fixed_y", default=0))

        btn_map_rev = {"left": "左键", "right": "右键", "middle": "中键"}
        self._button_combo.setCurrentText(
            btn_map_rev.get(config.get("clicker", "mouse_button", default="left"), "左键"))

        ct = config.get("clicker", "click_type", default="single")
        self._click_type_combo.setCurrentText("双击" if ct == "double" else "单击")

        count = config.get("clicker", "click_count", default=0)
        if count > 0:
            self._limited_rb.setChecked(True)
            self._count_spin.setValue(count)

    def save_settings(self):
        params = self._collect_params()
        for k, v in params.items():
            config.set("clicker", k, value=v)

    def get_params(self) -> dict:
        return {"clicker": self._collect_params()}

    def apply_params(self, params: dict):
        c = params.get("clicker", params)
        if "interval_ms" in c:
            self._interval_spin.setValue(c["interval_ms"])
        if "click_mode" in c:
            (self._fixed_rb if c["click_mode"] == "fixed" else self._follow_rb).setChecked(True)
        if "fixed_x" in c:
            self._fixed_x.setValue(c["fixed_x"])
        if "fixed_y" in c:
            self._fixed_y.setValue(c["fixed_y"])
        if "mouse_button" in c:
            self._button_combo.setCurrentText(c["mouse_button"])
        if "click_type" in c:
            self._click_type_combo.setCurrentText(c["click_type"])
        if "click_count" in c:
            count = c["click_count"]
            if count > 0:
                self._limited_rb.setChecked(True)
                self._count_spin.setValue(count)

    # ═══════════════════════════════════════════
    # 工具方法
    # ═══════════════════════════════════════════

    @staticmethod
    def _update_btn_style(widget, object_name: str):
        widget.setObjectName(object_name)
        widget.style().unpolish(widget)
        widget.style().polish(widget)

    def cleanup(self):
        self._stop_engine()
        if self._pick_timer:
            self._pick_timer.stop()
        hotkey_engine.unregister("clicker_toggle")
