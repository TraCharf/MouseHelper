"""
全局配置读写模块
使用 JSON 文件存储在 %APPDATA%/MouseHelper/ 目录
"""

import json
import os
from copy import deepcopy
from pathlib import Path
from typing import Any


class Config:
    """全局配置管理类（JSON 文件存储，线程安全）"""

    APP_NAME = "MouseHelper"

    DEFAULT_CONFIG: dict[str, Any] = {
        "hotkeys": {
            "clicker_toggle": "f6",
            "recorder_toggle": "f7",
            "player_toggle": "f8",
            "emergency_stop": "esc",
        },
        "general": {
            "theme": "dark",
            "language": "zh_CN",
            "close_to_tray": True,
            "start_minimized": False,
        },
        "clicker": {
            "interval_ms": 100,
            "click_mode": "follow",
            "fixed_x": 0,
            "fixed_y": 0,
            "mouse_button": "left",
            "click_count": 0,
            "click_type": "single",
        },
        "player": {
            "speed": 1.0,
            "loop_count": 1,
        },
    }

    def __init__(self):
        self._data_dir = Path(os.environ.get("APPDATA", ".")) / self.APP_NAME
        self._config_path = self._data_dir / "config.json"
        self._data: dict[str, Any] = {}
        self._ensure_data_dir()
        self.load()

    @property
    def data_dir(self) -> Path:
        return self._data_dir

    # ── 文件操作 ──

    def load(self):
        """从文件加载配置，失败则使用默认值"""
        if self._config_path.exists():
            try:
                with open(self._config_path, "r", encoding="utf-8") as f:
                    loaded = json.load(f)
                self._data = self._deep_merge(self.DEFAULT_CONFIG, loaded)
            except (json.JSONDecodeError, OSError):
                self._data = deepcopy(self.DEFAULT_CONFIG)
        else:
            self._data = deepcopy(self.DEFAULT_CONFIG)
            self.save()

    def save(self):
        """保存配置到文件"""
        self._ensure_data_dir()
        try:
            with open(self._config_path, "w", encoding="utf-8") as f:
                json.dump(self._data, f, ensure_ascii=False, indent=2)
        except OSError:
            pass  # 磁盘满等极端情况，静默失败

    # ── 读写接口 ──

    def get(self, *keys: str, default: Any = None) -> Any:
        """通过层级 key 获取配置值，如 config.get('hotkeys', 'clicker_toggle')"""
        node = self._data
        for key in keys:
            if isinstance(node, dict) and key in node:
                node = node[key]
            else:
                return default
        return node

    def set(self, *keys: str, value: Any):
        """设置配置值并自动保存"""
        if not keys:
            return
        node = self._data
        for key in keys[:-1]:
            if key not in node or not isinstance(node[key], dict):
                node[key] = {}
            node = node[key]
        node[keys[-1]] = value
        self.save()

    def get_all(self) -> dict:
        """获取全部配置的深拷贝"""
        return deepcopy(self._data)

    def reset(self):
        """重置为默认配置"""
        self._data = deepcopy(self.DEFAULT_CONFIG)
        self.save()

    # ── 内部 ──

    def _ensure_data_dir(self):
        self._data_dir.mkdir(parents=True, exist_ok=True)

    @classmethod
    def _deep_merge(cls, base: dict, override: dict) -> dict:
        """递归深度合并两个字典，override 覆盖 base"""
        result = deepcopy(base)
        for key, value in override.items():
            if (key in result and isinstance(result[key], dict)
                    and isinstance(value, dict)):
                result[key] = cls._deep_merge(result[key], value)
            else:
                result[key] = deepcopy(value)
        return result


# 全局单例
config = Config()
