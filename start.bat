@echo off
cd /d "%~dp0"
chcp 65001 >nul
title AI EXAM CONTROL - Multi-Camera System Launcher

echo ===============================================================================
echo                AI EXAM CONTROL - MULTI-CAMERA SYSTEM LAUNCHER
echo ===============================================================================
echo.

:: 1. Kiem tra Python va moi truong ao .venv
if exist ".venv\Scripts\python.exe" goto CHECK_FRONTEND

echo [THONG BAO] Chua tim thay moi truong ao .venv tai thu muc goc.
where python >nul 2>nul
if errorlevel 1 (
    echo [LOI] Khong tim thay Python tren he thong!
    echo Vui long cai dat Python 3.10 tro len va tich chon "Add Python to PATH".
    echo Download tai: https://www.python.org/downloads/
    echo.
    pause
    exit /b 1
)

echo [1/2] Dang khoi tao moi truong ao Python .venv...
python -m venv .venv
if errorlevel 1 (
    echo [LOI] Khoi tao .venv that bai. Vui long kiem tra quyen truy cap.
    pause
    exit /b 1
)

echo [2/2] Dang cai dat thu vien backend tu requirements.txt...
.venv\Scripts\python.exe -m pip install --upgrade pip
.venv\Scripts\python.exe -m pip install -r backend/requirements.txt
if errorlevel 1 (
    echo [CANH BAO] Co loi khi cai dat mot so thu vien, vui long kiem tra lai ket noi mang.
    pause
)
echo [HOAN TAT] Da thiet lap xong moi truong .venv!
echo.

:CHECK_FRONTEND
:: 2. Kiem tra Frontend dependencies (node_modules)
if exist "node_modules" goto LAUNCH_SYSTEM

where npm >nul 2>nul
if not errorlevel 1 (
    echo [INFO] Dang cai dat thu vien Frontend bang npm install...
    call npm install
    echo.
)

:LAUNCH_SYSTEM
echo [1/3] Khoi dong Backend AI Engine tai cong 8000...
start "AI Exam - Backend (:8000)" cmd /k "chcp 65001 >nul && cd /d "%~dp0" && .venv\Scripts\python.exe -m uvicorn main:app --app-dir backend --host 0.0.0.0 --port 8000"

echo [2/3] Khoi dong Frontend Proctor Dashboard tai cong 3000...
start "AI Exam - Frontend (:3000)" cmd /k "chcp 65001 >nul && cd /d "%~dp0" && npm run dev"

echo [3/3] Dang khoi tao camera va cho he thong san sang...
ping 127.0.0.1 -n 4 >nul

echo.
echo ===============================================================================
echo [THANH CONG] He thong da duoc khoi dong hoan tat!
echo - Giao dien Giam thi: http://localhost:3000
echo - Backend AI Engine:   http://localhost:8000
echo - Trang thai Camera:   http://localhost:8000/api/camera/sources
echo.
echo Tu dong mo trinh duyet...
echo ===============================================================================
start http://localhost:3000

echo.
echo (De dung he thong bat ky luc nao, hay chay file 'stop.bat' hoac dong 2 cua so cmd)
echo.
pause
