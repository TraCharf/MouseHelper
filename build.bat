@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

echo ============================================
echo   鼠标控制助手 - 一键打包脚本
echo ============================================
echo.

:: 检查 Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [错误] 未找到 Python，请先安装 Python 3.11+
    pause
    exit /b 1
)
echo [✓] Python 就绪

:: 安装依赖
echo [1/3] 安装依赖...
pip install -r requirements.txt -q 2>nul
if %errorlevel% neq 0 (
    echo [警告] 部分依赖安装失败，继续打包...
)
echo [✓] 依赖就绪

:: 打包
echo.
echo 请选择打包模式:
echo   [1] 文件夹模式 - 启动极快，含依赖目录 (推荐)
echo   [2] 单文件模式 - 单个exe，启动稍慢但便于分发
echo.
set /p MODE="请输入 [1] 或 [2] (默认=1): "
if "%MODE%"=="" set MODE=1
if "%MODE%"=="2" goto onefile
goto onedir

:onedir
echo [2/3] 打包（文件夹模式 - 启动极快）...
set BUILD_MODE=--onedir
set OUTPUT_DIR=dist\鼠标控制助手
goto build

:onefile
echo [2/3] 打包（单文件模式 - 启动稍慢）...
set BUILD_MODE=--onefile
set OUTPUT_DIR=dist
goto build

:build
pyinstaller %BUILD_MODE% ^
    --windowed ^
    --name "MouseHelper" ^
    --add-data "resources;resources" ^
    --clean ^
    --noconfirm ^
    --strip ^
    --exclude-module matplotlib ^
    --exclude-module numpy ^
    --exclude-module pandas ^
    --exclude-module PIL ^
    --exclude-module PyQt5 ^
    --exclude-module PyQt6 ^
    --exclude-module pygame ^
    --exclude-module IPython ^
    --exclude-module jupyter ^
    main.py

if %errorlevel% neq 0 (
    echo [错误] 打包失败！
    pause
    exit /b 1
)

echo [✓] 打包成功

:: 重命名
if exist "dist\MouseHelper" (
    ren "dist\MouseHelper" "鼠标控制助手" 2>nul
)
if exist "dist\MouseHelper.exe" (
    ren "dist\MouseHelper.exe" "鼠标控制助手.exe" 2>nul
)

echo [3/3] 完成！
echo.
echo ============================================
echo   打包完成！输出: %OUTPUT_DIR%
echo ============================================
echo.
echo 提示：
echo   - 双击即可运行，无命令行黑窗
echo   - 全局热键需要管理员权限
echo.
pause
