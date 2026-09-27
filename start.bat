@echo off
chcp 65001 >nul
title AI EXAM CONTROL - Multi-Camera System Launcher
echo ===============================================================================
echo                AI EXAM CONTROL - MULTI-CAMERA SYSTEM LAUNCHER
echo ===============================================================================
echo.

cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    echo [LOI] Khong tim thay moi truong ao .venv tai thu muc goc!
    echo Vui long kiem tra lai moi truong Python.
    pause
    exit /b 1
)

echo [1/3] Khoi dong Backend AI Engine (FastAPI tren cong 8000)...
start "AI Exam - Backend (:8000)" cmd /k "chcp 65001 >nul && cd /d "%~dp0" && .venv\Scripts\python.exe -m uvicorn main:app --app-dir backend --host 0.0.0.0 --port 8000"

echo [2/3] Khoi dong Frontend Proctor Dashboard (Vite tren cong 3000)...
start "AI Exam - Frontend (:3000)" cmd /k "chcp 65001 >nul && cd /d "%~dp0" && npm run dev"

echo [3/3] Dang khoi tao camera va cho he thong san sang...
timeout /t 3 /nobreak >nul

echo.
echo ===============================================================================
echo [THANH CONG] He thong da duoc khoi dong hoan tat!
echo - Giao dien Giam thi: http://localhost:3000
echo - Backend AI Engine:   http://localhost:8000
echo - Trạng thái Camera:   http://localhost:8000/api/camera/sources
echo.
echo Tu dong mo trinh duyet...
echo ===============================================================================
start http://localhost:3000

echo.
echo (De dung he thong bat ky luc nao, hay chay file 'stop.bat' hoac dong 2 cua so cmd)
echo.
pause
