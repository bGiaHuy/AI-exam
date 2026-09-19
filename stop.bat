@echo off
chcp 65001 > nul
setlocal enabledelayedexpansion

title AI Exam Control - Stop Services
cd /d "%~dp0"

echo ================================================================================
echo           DỪNG HỆ THỐNG AI EXAM CONTROL
echo ================================================================================
echo.

echo [INFO] Đang đóng các tiến trình chạy trên cổng 8000 (Backend)...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :8000 ^| findstr LISTENING') do (
    taskkill /F /PID %%a >nul 2>&1
)

echo [INFO] Đang đóng các tiến trình chạy trên cổng 3000 (Frontend)...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :3000 ^| findstr LISTENING') do (
    taskkill /F /PID %%a >nul 2>&1
)

echo [INFO] Đang đóng các cửa sổ AI-Exam...
taskkill /FI "WINDOWTITLE eq AI-Exam Backend*" /T /F >nul 2>&1
taskkill /FI "WINDOWTITLE eq AI-Exam Frontend*" /T /F >nul 2>&1

echo.
echo [DONE] Toàn bộ dịch vụ Backend và Frontend đã được dừng thành công.
echo ================================================================================
timeout /t 3 > nul
