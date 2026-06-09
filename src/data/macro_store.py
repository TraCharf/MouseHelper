"""
宏脚本存取模块
宏文件以 .mmacro JSON 格式存储
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any
from src.data.config import config


class MacroStore:
    """宏脚本管理器"""

    EXTENSION = ".mmacro"

    def __init__(self):
        self._macros_dir = config.data_dir / "macros"
        self._macros_dir.mkdir(parents=True, exist_ok=True)

    @property
    def macros_dir(self) -> Path:
        return self._macros_dir

    def list_macros(self) -> list[dict[str, Any]]:
        """列出所有宏脚本"""
        macros = []
        for f in sorted(self._macros_dir.glob(f"*{self.EXTENSION}")):
            try:
                with open(f, "r", encoding="utf-8") as fp:
                    data = json.load(fp)
                macros.append({
                    "name": f.stem,
                    "path": str(f),
                    "created": data.get("created", "未知"),
                    "action_count": len(data.get("actions", [])),
                    "description": data.get("description", ""),
                })
            except Exception:
                continue
        return macros

    def save_macro(self, name: str, actions: list[dict], description: str = ""):
        """保存宏脚本"""
        data = {
            "name": name,
            "description": description,
            "created": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "actions": actions,
        }
        filepath = self._macros_dir / f"{name}{self.EXTENSION}"
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def load_macro(self, name: str) -> dict[str, Any] | None:
        """加载宏脚本"""
        filepath = self._macros_dir / f"{name}{self.EXTENSION}"
        if not filepath.exists():
            return None
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)

    def delete_macro(self, name: str) -> bool:
        """删除宏脚本"""
        filepath = self._macros_dir / f"{name}{self.EXTENSION}"
        if filepath.exists():
            filepath.unlink()
            return True
        return False

    def rename_macro(self, old_name: str, new_name: str) -> bool:
        """重命名宏脚本"""
        old_path = self._macros_dir / f"{old_name}{self.EXTENSION}"
        new_path = self._macros_dir / f"{new_name}{self.EXTENSION}"
        if old_path.exists() and not new_path.exists():
            old_path.rename(new_path)
            return True
        return False


# 全局单例
macro_store = MacroStore()
