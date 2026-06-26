@echo off
chcp 65001 > nul
title 抖音AI自动回复系统
color 0A
cls
echo ================================================
echo.
echo        抖音私信自动回复系统 v2.0
echo.
echo ================================================
echo.
echo 功能说明：
echo   - 自动接收私信
echo   - AI智能回复（真人风格）
echo   - 知识库回复
echo   - WebSocket实时监听
echo.
echo ================================================
echo.
echo 启动中...
echo.
timeout /t 2 /nobreak > nul
python dy_apis\douyin_recv_ai.py
echo.
echo.
echo 系统已退出
pause