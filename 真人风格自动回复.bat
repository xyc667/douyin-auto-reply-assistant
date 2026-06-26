@echo off
chcp 65001 > nul
echo ==============================================================
echo.
echo        🤖 抖音AI真人风格自动回复系统
echo.
echo ==============================================================
echo.
echo 配置已优化为真人聊天风格，避免风控！
echo.

# 进入目录
cd /d "%~dp0"

# 检查Python
python --version > nul 2>&1
if errorlevel 1 (
    echo ❌ Python未安装
    pause
    exit /b 1
)

echo.
echo ✅ Python已安装
echo.
echo 配置优化内容：
echo    - 延迟8-20秒（更像真人打字）
echo    - 语气词：嗯嗯、哈哈、好的
echo    - 表情符号：👌 😊 👍
echo    - 短句回复（5-15字）
echo.
echo ==============================================================
echo.
echo 启动中...
echo.
timeout /t 2
python dy_apis\douyin_recv_ai.py

pause