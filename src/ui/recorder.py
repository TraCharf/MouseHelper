"""
录制与回放页面
"""

import json
from pathlib import Path

from PySide6.QtCore import Qt, Signal, QObject
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QLabel,
    QPushButton, QListWidget, QDoubleSpinBox, QSpinBox,
    QFileDialog, QMessageBox,
)

from src.core.recorder_engine import RecorderEngine
from src.core.player_engine import PlayerEngine
from src.core.hotkey_engine import hotkey_engine
from src.data.config import config


class RecorderPage(QWidget):
    """录制与回放页面"""

    # 从 pynput 线程安全投递录制事件到 Qt 主线程
    _event_received = Signal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._recorder = RecorderEngine()
        self._player: PlayerEngine | None = None
        self._recorded_events: list[dict] = []
        self._current_file: str = ""

        self._setup_ui()
        self._connect_signals()
        self._register_hotkeys()

    # ═══════════════════════════════════════════
    # UI 构建
    # ═══════════════════════════════════════════

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 16, 20, 16)
        main_layout.setSpacing(12)

        title = QLabel("录制与回放")
        title.setObjectName("titleLabel")
        main_layout.addWidget(title)

        # ── 录制 ──
        record_group = QGroupBox("录制")
        record_layout = QVBoxLayout(record_group)

        info_layout = QHBoxLayout()
        self._record_status = QLabel("⏸️ 未录制")
        info_layout.addWidget(self._record_status)
        info_layout.addStretch()
        self._event_count_label = QLabel("事件数: 0")
        info_layout.addWidget(self._event_count_label)
        self._duration_label = QLabel("时长: 0.0s")
        info_layout.addWidget(self._duration_label)
        record_layout.addLayout(info_layout)

        btn_layout = QHBoxLayout()
        self._record_btn = QPushButton("⏺️ 开始录制")
        self._record_btn.setObjectName("dangerBtn")
        self._record_btn.clicked.connect(self._toggle_recording)
        btn_layout.addWidget(self._record_btn)
        self._save_btn = QPushButton("💾 保存录制")
        self._save_btn.clicked.connect(self._save_recording)
        self._save_btn.setEnabled(False)
        btn_layout.addWidget(self._save_btn)
        self._clear_btn = QPushButton("🗑️ 清除")
        self._clear_btn.clicked.connect(self._clear_recording)
        self._clear_btn.setEnabled(False)
        btn_layout.addWidget(self._clear_btn)
        hotkey = config.get("hotkeys", "recorder_toggle", default="F7")
        self._rec_hotkey_label = QLabel(f"快捷键: [{hotkey.upper()}]")
        self._rec_hotkey_label.setStyleSheet("color: #2ecc71;")
        btn_layout.addWidget(self._rec_hotkey_label)
        btn_layout.addStretch()
        record_layout.addLayout(btn_layout)
        main_layout.addWidget(record_group)

        # ── 事件列表 ──
        event_group = QGroupBox("录制事件列表")
        event_layout = QVBoxLayout(event_group)
        self._event_list = QListWidget()
        self._event_list.setMaximumHeight(200)
        event_layout.addWidget(self._event_list)
        main_layout.addWidget(event_group)

        # ── 回放 ──
        play_group = QGroupBox("回放")
        play_layout = QVBoxLayout(play_group)

        settings_layout = QHBoxLayout()
        settings_layout.addWidget(QLabel("回放速度:"))
        self._speed_spin = QDoubleSpinBox()
        self._speed_spin.setRange(0.1, 10.0)
        self._speed_spin.setValue(1.0)
        self._speed_spin.setSingleStep(0.1)
        self._speed_spin.setSuffix("x")
        settings_layout.addWidget(self._speed_spin)
        settings_layout.addWidget(QLabel("循环次数:"))
        self._loop_spin = QSpinBox()
        self._loop_spin.setRange(0, 999)
        self._loop_spin.setValue(1)
        self._loop_spin.setSuffix(" 次")
        self._loop_spin.setSpecialValueText("无限")  # 0 = 无限循环
        settings_layout.addWidget(self._loop_spin)
        settings_layout.addStretch()
        play_layout.addLayout(settings_layout)

        btn_layout2 = QHBoxLayout()
        self._load_btn = QPushButton("📂 加载录制文件")
        self._load_btn.clicked.connect(self._load_recording)
        btn_layout2.addWidget(self._load_btn)
        self._play_btn = QPushButton("▶ 开始回放")
        self._play_btn.setObjectName("primaryBtn")
        self._play_btn.clicked.connect(self._toggle_playback)
        self._play_btn.setEnabled(False)
        btn_layout2.addWidget(self._play_btn)
        hotkey2 = config.get("hotkeys", "player_toggle", default="F8")
        self._play_hotkey_label = QLabel(f"快捷键: [{hotkey2.upper()}]")
        self._play_hotkey_label.setStyleSheet("color: #2ecc71;")
        btn_layout2.addWidget(self._play_hotkey_label)
        self._progress_label = QLabel("")
        btn_layout2.addWidget(self._progress_label)
        btn_layout2.addStretch()
        play_layout.addLayout(btn_layout2)

        self._play_status = QLabel("⏸️ 未回放")
        play_layout.addWidget(self._play_status)
        main_layout.addWidget(play_group)
        main_layout.addStretch()

    # ═══════════════════════════════════════════
    # 信号连接
    # ═══════════════════════════════════════════

    def _connect_signals(self):
        # 录制事件通过信号安全投递到主线程
        self._recorder.set_event_callback(lambda e: self._event_received.emit(e))
        self._event_received.connect(self._on_record_event)

    # ═══════════════════════════════════════════
    # 录制控制
    # ═══════════════════════════════════════════

    def _toggle_recording(self):
        if self._recorder.is_recording:
            self._recorded_events = self._recorder.stop()
            self._record_btn.setText("⏺️ 开始录制")
            self._set_btn_style(self._record_btn, "dangerBtn")
            self._record_status.setText("⏸️ 录制已停止")
            has_events = len(self._recorded_events) > 0
            self._save_btn.setEnabled(has_events)
            self._clear_btn.setEnabled(has_events)
            self._play_btn.setEnabled(has_events)
            self._duration_label.setText(f"时长: {self._recorder.duration:.1f}s")
        else:
            self._event_list.clear()
            self._recorded_events = []
            self._current_file = ""
            self._recorder.start()
            self._record_btn.setText("⏹ 停止录制")
            self._set_btn_style(self._record_btn, "successBtn")
            self._record_status.setText("🔴 录制中...")
            self._save_btn.setEnabled(False)
            self._clear_btn.setEnabled(False)
            self._play_btn.setEnabled(False)

    def _on_record_event(self, event: dict):
        """在主线程更新事件列表"""
        ts = event.get("timestamp", 0)
        etype = event.get("type", "?")
        item_text = f"[{ts:.2f}s] {etype}"
        if etype == "move":
            item_text += f" → ({event.get('x', 0)}, {event.get('y', 0)})"
        elif etype == "click":
            item_text += (f" {event.get('button', '?')} "
                          f"{'按下' if event.get('pressed') else '释放'}"
                          f" at ({event.get('x', 0)}, {event.get('y', 0)})")
        elif etype == "scroll":
            item_text += f" dy={event.get('dy', 0)}"
        self._event_list.addItem(item_text)
        self._event_list.scrollToBottom()
        self._event_count_label.setText(f"事件数: {self._recorder.event_count}")

    def _save_recording(self):
        if not self._recorded_events:
            return
        filepath, _ = QFileDialog.getSaveFileName(
            self, "保存录制", str(Path.home() / "Desktop"), "录制文件 (*.mrec)")
        if filepath:
            if not filepath.endswith(".mrec"):
                filepath += ".mrec"
            data = self._recorder.export_data()
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            self._current_file = filepath
            QMessageBox.information(self, "保存成功", f"录制已保存到:\n{filepath}")

    def _load_recording(self):
        filepath, _ = QFileDialog.getOpenFileName(
            self, "加载录制文件", str(Path.home() / "Desktop"),
            "录制文件 (*.mrec);;所有文件 (*.*)")
        if not filepath:
            return
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
            self._recorded_events = data.get("events", [])
            self._current_file = filepath
            self._event_list.clear()
            for evt in self._recorded_events:
                self._on_record_event(evt)
            self._event_count_label.setText(f"事件数: {len(self._recorded_events)}")
            self._play_btn.setEnabled(True)
            self._save_btn.setEnabled(True)
            QMessageBox.information(self, "加载成功",
                                    f"已加载 {len(self._recorded_events)} 个事件")
        except Exception as e:
            QMessageBox.critical(self, "加载失败", f"无法加载文件:\n{e}")

    def _clear_recording(self):
        self._recorded_events = []
        self._current_file = ""
        self._event_list.clear()
        self._event_count_label.setText("事件数: 0")
        self._duration_label.setText("时长: 0.0s")
        self._save_btn.setEnabled(False)
        self._clear_btn.setEnabled(False)
        self._play_btn.setEnabled(False)

    # ═══════════════════════════════════════════
    # 回放控制
    # ═══════════════════════════════════════════

    def _toggle_playback(self):
        if self._player and self._player.isRunning():
            self._player.stop()
            self._player = None
        else:
            if not self._recorded_events:
                QMessageBox.warning(self, "无数据", "请先录制或加载录制文件")
                return
            # QThread 不可重用，每次创建新实例
            self._player = PlayerEngine(
                events=list(self._recorded_events),
                speed=self._speed_spin.value(),
                loop_count=self._loop_spin.value(),
            )
            self._player.started.connect(self._on_play_started)
            self._player.stopped.connect(self._on_play_stopped)
            self._player.progress.connect(self._on_play_progress)
            self._player.start()

    def _on_play_started(self):
        self._play_btn.setText("⏹ 停止回放")
        self._set_btn_style(self._play_btn, "dangerBtn")
        self._play_status.setText("🟢 回放中...")
        self._play_status.setStyleSheet("color: #2ecc71; font-weight: bold;")

    def _on_play_stopped(self):
        self._play_btn.setText("▶ 开始回放")
        self._set_btn_style(self._play_btn, "primaryBtn")
        self._play_status.setText("⏸️ 回放已停止")
        self._play_status.setStyleSheet("")
        self._progress_label.setText("")
        self._player = None

    def _on_play_progress(self, current: int, total: int):
        self._progress_label.setText(f"进度: {current}/{total}")

    # ═══════════════════════════════════════════
    # 热键
    # ═══════════════════════════════════════════

    def _register_hotkeys(self):
        hotkey_engine.register(
            "recorder_toggle",
            config.get("hotkeys", "recorder_toggle", default="f7"),
            self._toggle_recording,
        )
        hotkey_engine.register(
            "player_toggle",
            config.get("hotkeys", "player_toggle", default="f8"),
            self._toggle_playback,
        )

    # ═══════════════════════════════════════════
    # 预设/配置
    # ═══════════════════════════════════════════

    def save_settings(self):
        config.set("player", "speed", value=self._speed_spin.value())
        config.set("player", "loop_count", value=self._loop_spin.value())

    def get_params(self) -> dict:
        return {"player": {"speed": self._speed_spin.value(),
                           "loop_count": self._loop_spin.value()}}

    def apply_params(self, params: dict):
        p = params.get("player", params)
        if "speed" in p:
            self._speed_spin.setValue(p["speed"])
        if "loop_count" in p:
            self._loop_spin.setValue(p["loop_count"])

    # ═══════════════════════════════════════════
    # 工具
    # ═══════════════════════════════════════════

    @staticmethod
    def _set_btn_style(btn, object_name: str):
        btn.setObjectName(object_name)
        btn.style().unpolish(btn)
        btn.style().polish(btn)

    def cleanup(self):
        if self._recorder.is_recording:
            self._recorder.stop()
        if self._player:
            self._player.stop()
            self._player = None
        hotkey_engine.unregister("recorder_toggle")
        hotkey_engine.unregister("player_toggle")
