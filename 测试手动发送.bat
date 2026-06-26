@echo off
chcp 65001 > nul
cd /d "%~dp0"
echo.
echo ==============================================================
echo.
echo        🧪 手动发送测试
echo.
echo ==============================================================
echo.
echo 测试手动发送功能...
echo.
python test_send.py
echo.
pause
