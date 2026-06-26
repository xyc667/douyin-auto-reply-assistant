@echo off
chcp 65001 > nul
echo.
echo ==============================================================
echo.
echo        🤖 抖音AI自动回复系统 - 快速启动
echo.
echo ==============================================================
echo.

REM 检查Python是否安装
python --version > nul 2>&1
if errorlevel 1 (
    echo ❌ Python未安装，请先安装Python 3.7+
    pause
    exit /b 1
)

echo ✅ Python已安装
echo.

REM 检查必要的文件
if not exist "config_ai.env" (
    echo ❌ 配置文件不存在！
    echo    请先配置 config_ai.env 文件
    echo    特别是设置 ANTHROPIC_API_KEY
    echo.
    echo 操作步骤：
    echo 1. 编辑 config_ai.env 文件
    echo 2. 设置你的 API_KEY
    echo 3. 保存后重新运行此脚本
    echo.
    notepad config_ai.env
    pause
    exit /b 1
)

REM 检查API Key
findstr /C:"ANTHROPIC_API_KEY=" config_ai.env > nul
if errorlevel 1 (
    echo ❌ API Key未配置！
    echo.
    echo 请编辑 config_ai.env 设置你的API Key：
    echo   ANTHROPIC_API_KEY=你的API_Key
    echo.
    notepad config_ai.env
    pause
    exit /b 1
)

REM 检查必要的库
echo 🔍 检查依赖库...
pip show requests > nul 2>&1
if errorlevel 1 (
    echo 📦 安装必要库...
    pip install requests
)

echo.
echo ==============================================================
echo.
echo  选择运行模式：
echo.
echo    [1] 🚀 AI自动回复系统（接收+AI回复+发送）
echo    [2] 🧪 仅测试AI连接
echo    [3] 📊 查看日志
echo    [4] ❌ 退出
echo.
echo ==============================================================
echo.

set /p choice=请输入选项 (1-4): 

if "%choice%"=="1" goto :run_full
if "%choice%"=="2" goto :test_ai
if "%choice%"=="3" goto :view_log
if "%choice%"=="4" goto :exit

:run_full
echo.
echo 🚀 启动AI自动回复系统...
echo.
python dy_apis/douyin_recv_ai.py
goto :end

:test_ai
echo.
echo 🧪 测试AI连接...
echo.
python ai_auto_reply.py
goto :end

:view_log
echo.
echo 📊 查看最近日志...
echo.
if exist "datas/reply_log.txt" (
    powershell -command "Get-Content datas/reply_log.txt -Tail 50"
) else (
    echo ❌ 日志文件不存在
)
echo.
pause
goto :run_again

:exit
echo.
echo 👋 再见！
echo.
exit /b 0

:end
pause

:run_again
echo.
echo.
echo 按任意键返回主菜单...
pause > nul
goto :start