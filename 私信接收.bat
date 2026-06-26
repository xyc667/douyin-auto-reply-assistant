@echo off
chcp 65001 > nul
cd /d "%~dp0"
echo.
echo 私信接收系统
echo.
python dy_apis\douyin_recv_msg.py
pause