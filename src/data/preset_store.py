"""
预设方案存取模块
每个预设是一个 JSON 文件，包含所有页面的参数
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any
from src.data.config import config


class PresetStore:
    """预设方案管理器"""

    EXTENSION = ".mpre"

    def __init__(self):
        self._presets_dir = config.data_dir / "presets"
        self._presets_dir.mkdir(parents=True, exist_ok=True)

    @property
    def presets_dir(self) -> Path:
        return self._presets_dir

    def list_presets(self) -> list[dict[str, Any]]:
        """列出所有预设方案"""
        presets = []
        for f in sorted(self._presets_dir.glob(f"*{self.EXTENSION}")):
            try:
                with open(f, "r", encoding="utf-8") as fp:
                    data = json.load(fp)
                presets.append({
                    "name": f.stem,
                    "path": str(f),
                    "created": data.get("created", "未知"),
                    "description": data.get("description", ""),
                })
            except Exception:
                continue
        return presets

    def save_preset(self, name: str, params: dict[str, Any], description: str = ""):
        """保存预设方案"""
        data = {
            "name": name,
            "description": description,
            "created": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "params": params,
        }
        filepath = self._presets_dir / f"{name}{self.EXTENSION}"
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def load_preset(self, name: str) -> dict[str, Any] | None:
        """加载预设方案"""
        filepath = self._presets_dir / f"{name}{self.EXTENSION}"
        if not filepath.exists():
            return None
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)

    def delete_preset(self, name: str) -> bool:
        """删除预设方案"""
        filepath = self._presets_dir / f"{name}{self.EXTENSION}"
        if filepath.exists():
            filepath.unlink()
            return True
        return False

    def export_preset(self, name: str, export_path: str) -> bool:
        """导出预设到指定路径"""
        filepath = self._presets_dir / f"{name}{self.EXTENSION}"
        if not filepath.exists():
            return False
        import shutil
        shutil.copy(filepath, export_path)
        return True

    def import_preset(self, import_path: str) -> str | None:
        """从文件导入预设，返回预设名称"""
        src = Path(import_path)
        if not src.exists():
            return None
        with open(src, "r", encoding="utf-8") as f:
            data = json.load(f)
        name = data.get("name", src.stem)
        dst = self._presets_dir / f"{name}{self.EXTENSION}"
        import shutil
        shutil.copy(src, dst)
        return name


# 全局单例
preset_store = PresetStore()
