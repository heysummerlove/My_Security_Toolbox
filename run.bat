@echo off
chcp 65001 >nul
title 离线安全单兵系统 - 启动终端
cd /d "%~dp0"

echo ========================================
echo [1/3] 正在执行运行环境安全体检...
echo ========================================
.\runtime\python.exe env_check.py
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [❌] 环境自检未通过，工具箱启动已中止！请查阅上方报错信息。
    pause
    exit /b
)

echo.
echo ========================================
echo [2/3] 体检通过，启动 API 调度中枢...
echo ========================================
:: 强制 Python 使用 UTF-8 输出日志，防止后台乱码
start /b cmd /c "set PYTHONIOENCODING=utf-8 && .\runtime\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8080"

timeout /t 2 /nobreak >nul

echo.
echo ========================================
echo [3/3] 启动前端控制台...
echo ========================================
start http://127.0.0.1:8080

echo 运行中... (请勿关闭此黑窗口)
pause >nul