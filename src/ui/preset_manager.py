"""
预设管理页面
保存/加载/导入/导出预设方案
"""

from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QLabel,
    QPushButton, QListWidget, QListWidgetItem, QFileDialog, QMessageBox,
    QLineEdit, QInputDialog,
)

from src.data.preset_store import preset_store


class PresetManagerPage(QWidget):
    """预设管理页面"""

    preset_loaded = Signal(dict)   # 加载预设时发射
    save_requested = Signal(str, str)  # 保存预设时发射 (name, description)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
        self._refresh_list()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 16, 20, 16)
        main_layout.setSpacing(12)

        title = QLabel("预设管理")
        title.setObjectName("titleLabel")
        main_layout.addWidget(title)

        # 说明
        hint = QLabel("预设方案可以保存当前所有页面的参数配置，方便快速切换使用场景")
        hint.setObjectName("hintLabel")
        hint.setWordWrap(True)
        main_layout.addWidget(hint)

        # === 预设列表 ===
        list_group = QGroupBox("已保存的预设")
        list_layout = QVBoxLayout(list_group)
        self._preset_list = QListWidget()
        self._preset_list.setMinimumHeight(200)
        list_layout.addWidget(self._preset_list)

        # 操作按钮
        btn_layout = QHBoxLayout()
        self._save_btn = QPushButton("💾 保存当前配置")
        self._save_btn.setObjectName("primaryBtn")
        self._save_btn.clicked.connect(self._save_current)
        btn_layout.addWidget(self._save_btn)

        self._load_btn = QPushButton("📥 加载选中预设")
        self._load_btn.clicked.connect(self._load_selected)
        btn_layout.addWidget(self._load_btn)

        self._delete_btn = QPushButton("🗑️ 删除")
        self._delete_btn.clicked.connect(self._delete_selected)
        btn_layout.addWidget(self._delete_btn)
        btn_layout.addStretch()
        list_layout.addLayout(btn_layout)
        main_layout.addWidget(list_group)

        # === 导入导出 ===
        io_group = QGroupBox("导入/导出")
        io_layout = QHBoxLayout(io_group)
        self._export_btn = QPushButton("📤 导出选中预设")
        self._export_btn.clicked.connect(self._export_selected)
        io_layout.addWidget(self._export_btn)

        self._import_btn = QPushButton("📥 导入预设文件")
        self._import_btn.clicked.connect(self._import_preset)
        io_layout.addWidget(self._import_btn)
        io_layout.addStretch()
        main_layout.addWidget(io_group)
        main_layout.addStretch()

    def _refresh_list(self):
        """刷新预设列表"""
        self._preset_list.clear()
        for preset in preset_store.list_presets():
            text = f"{preset['name']}"
            if preset.get("description"):
                text += f" - {preset['description']}"
            text += f" ({preset['created']})"
            item = QListWidgetItem(text)
            item.setData(Qt.ItemDataRole.UserRole, preset["name"])
            self._preset_list.addItem(item)

    def _save_current(self):
        """保存当前所有参数为预设"""
        name, ok = QInputDialog.getText(self, "保存预设", "请输入预设名称:")
        if not ok or not name.strip():
            return
        desc, ok2 = QInputDialog.getText(self, "保存预设", "请输入描述（可选）:")
        desc = desc if ok2 else ""

        # 发射信号让主窗口收集所有参数并保存
        self.save_requested.emit(name.strip(), desc)
        self._refresh_list()
        QMessageBox.information(self, "保存成功", f"预设 [{name}] 已保存")

    def _load_selected(self):
        """加载选中的预设"""
        item = self._preset_list.currentItem()
        if not item:
            QMessageBox.warning(self, "未选择", "请先选择一个预设")
            return
        name = item.data(Qt.ItemDataRole.UserRole)
        data = preset_store.load_preset(name)
        if data:
            self.preset_loaded.emit(data.get("params", {}))
            QMessageBox.information(self, "加载成功", f"预设 [{name}] 已加载")

    def _delete_selected(self):
        """删除选中的预设"""
        item = self._preset_list.currentItem()
        if not item:
            return
        name = item.data(Qt.ItemDataRole.UserRole)
        reply = QMessageBox.question(self, "确认删除", f"确定要删除预设 [{name}] 吗？")
        if reply == QMessageBox.StandardButton.Yes:
            preset_store.delete_preset(name)
            self._refresh_list()

    def _export_selected(self):
        """导出现有预设"""
        item = self._preset_list.currentItem()
        if not item:
            QMessageBox.warning(self, "未选择", "请先选择一个预设")
            return
        name = item.data(Qt.ItemDataRole.UserRole)
        filepath, _ = QFileDialog.getSaveFileName(
            self, "导出预设", str(Path.home() / "Desktop" / f"{name}.mpre"), "预设文件 (*.mpre)"
        )
        if filepath:
            if preset_store.export_preset(name, filepath):
                QMessageBox.information(self, "导出成功", f"已导出到:\n{filepath}")

    def _import_preset(self):
        """从文件导入预设"""
        filepath, _ = QFileDialog.getOpenFileName(
            self, "导入预设", str(Path.home() / "Desktop"), "预设文件 (*.mpre);;所有文件 (*.*)"
        )
        if filepath:
            name = preset_store.import_preset(filepath)
            if name:
                self._refresh_list()
                QMessageBox.information(self, "导入成功", f"已导入预设: {name}")

    def get_params(self) -> dict:
        return {}

    def apply_params(self, params: dict):
        pass

    def cleanup(self):
        pass
