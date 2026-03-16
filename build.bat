@echo off
chcp 65001 >nul
echo ========================================
echo CodeTraceAI 打包工具
echo ========================================
echo.

REM 检查 Python 是否安装
python --version >nul 2>&1
if errorlevel 1 (
    echo 错误: 未找到 Python，请先安装 Python
    pause
    exit /b 1
)

echo Python 版本:
python --version
echo.

REM 执行打包脚本
echo 开始打包...
python build_exe.py

echo.
echo ========================================
echo 打包流程结束
echo ========================================
pause
