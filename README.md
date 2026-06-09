<p align="center">
  <h1 align="center">🖱️ 鼠标控制助手</h1>
  <p align="center">功能齐全、适合小白使用的 Windows 鼠标控制工具</p>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/platform-Windows-blue?logo=windows" alt="Platform">
  <img src="https://img.shields.io/badge/python-3.11%2B-blue?logo=python" alt="Python">
  <img src="https://img.shields.io/badge/license-MIT-green" alt="License">
  <img src="https://img.shields.io/badge/version-1.0-red" alt="Version">
</p>

---

## 📥 下载

[**⬇️ 点击下载 (v1.0)**](https://github.com/TraCharf/MouseHelper/releases/latest)

> 备用下载：[https://888124.xyz/data](https://888124.xyz/data)

---

## ✨ 功能

| 功能 | 快捷键 | 说明 |
|------|--------|------|
| 🖱️ **自动连点器** | `F6` | 可调间隔/按键/坐标/次数，支持跟随鼠标或固定坐标 |
| ⏺️ **录制与回放** | `F7` `F8` | 录制鼠标操作，保存/加载，支持变速和循环回放 |
| 📝 **鼠标宏编辑** | — | 可视化编辑动作序列（移动/点击/等待/循环/按键） |
| 🔧 **光标工具** | — | 实时坐标、颜色拾取 (RGB/HEX)、光标高亮、屏幕标尺 |
| 📂 **预设管理** | — | 一键保存/加载/导入/导出所有配置方案 |
| ⚙️ **系统托盘** | — | 最小化到托盘，后台静默运行，托盘右键快速操作 |

## 🚀 快速开始

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 运行
python main.py

# 3. 打包成 exe（可选）
build.bat
```

## 📦 打包

运行 `build.bat`，选择模式：
- **文件夹模式**（推荐）— 启动极快，含 `_internal` 依赖目录
- **单文件模式** — 单个 exe，启动稍慢但便于分发

打包后在 `dist/` 目录获取 `鼠标控制助手/`。

## ⚠️ 提示

- 全局热键 (`F6`/`F7`/`F8`) 需要**管理员权限**：右键 → 以管理员身份运行
- 按 `Esc` 紧急停止所有功能
- 配置和数据存储在 `%APPDATA%\MouseHelper\`

## 🛠 技术栈

- **GUI:** PySide6 (Qt 6)
- **鼠标模拟:** PyAutoGUI
- **全局监听:** pynput
- **打包:** PyInstaller

## 📄 开源协议

MIT License © 2025 Fng

---

<p align="center">
  <a href="https://888124.xyz">888124.xyz</a>
</p>
