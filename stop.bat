@echo off
setlocal enabledelayedexpansion

title AI Exam Control - Stop Services
cd /d "%~dp0"

echo ================================================================================
echo           DUNG HE THONG AI EXAM CONTROL
echo ================================================================================
echo.

echo [INFO] Dang dong cac tien trinh chay tren cong 8000 (Backend)...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :8000 ^| findstr LISTENING') do (
    taskkill /F /PID %%a >nul 2>&1
)

echo [INFO] Dang dong cac tien trinh chay tren cong 3000 (Frontend)...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :3000 ^| findstr LISTENING') do (
    taskkill /F /PID %%a >nul 2>&1
)

echo [INFO] Dang dong cac cua so AI-Exam...
taskkill /FI "WINDOWTITLE eq AI-Exam Backend*" /T /F >nul 2>&1
taskkill /FI "WINDOWTITLE eq AI-Exam Frontend*" /T /F >nul 2>&1

echo.
echo [DONE] Toan bo dich vu Backend va Frontend da duoc dung thanh cong.
echo ================================================================================
ping 127.0.0.1 -n 3 > nul
