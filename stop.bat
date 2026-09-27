@echo off
chcp 65001 >nul
title AI EXAM CONTROL - System Stopper
echo ===============================================================================
echo                AI EXAM CONTROL - DUNG DICH VU
echo ===============================================================================
echo.

echo [1/2] Dang dung Backend (Port 8000)...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":8000" ^| findstr "LISTENING"') do (
    taskkill /f /pid %%a >nul 2>&1
)

echo [2/2] Dang dung Frontend (Port 3000)...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":3000" ^| findstr "LISTENING"') do (
    taskkill /f /pid %%a >nul 2>&1
)

echo.
echo ===============================================================================
echo [HOAN TAT] He thong Backend va Frontend da duoc dung sach se!
echo ===============================================================================
echo.
pause
