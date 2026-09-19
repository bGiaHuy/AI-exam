@echo off
setlocal enabledelayedexpansion

title AI Exam Control - Automated Proctoring System
cd /d "%~dp0"

echo ================================================================================
echo           HE THONG GIAM SAT THI CU THONG MINH - AI EXAM CONTROL
echo ================================================================================
echo.

:: 1. Kiem tra Python
where python >nul 2>nul
if %errorlevel% equ 0 goto CHECK_NODE
echo [ERROR] Khong tim thay Python tren he thong!
echo Vui long cai dat Python 3.10 tro len va tich chon Add Python to PATH.
echo Download tai: https://www.python.org/downloads/
pause
exit /b 1

:CHECK_NODE
:: 2. Kiem tra Node.js
where node >nul 2>nul
if %errorlevel% equ 0 goto CHECK_VENV
echo [ERROR] Khong tim thay Node.js tren he thong!
echo Vui long cai dat Node.js 18 tro len de chay giao dien Frontend.
echo Download tai: https://nodejs.org/
pause
exit /b 1

:CHECK_VENV
:: 3. Kiem tra moi truong ao Python
if exist ".venv\Scripts\python.exe" goto CHECK_FRONTEND

echo [INFO] Dang khoi tao moi truong ao Python .venv...
where uv >nul 2>nul
if %errorlevel% neq 0 goto USE_PIP

:: Su dung uv neu co
uv venv .venv
echo [INFO] Dang cai dat thu vien backend bang uv...
uv pip install -r backend/requirements.txt --python .venv\Scripts\python.exe
goto VERIFY_VENV

:USE_PIP
:: Su dung python standard venv va pip
python -m venv .venv
echo [INFO] Dang cai dat thu vien backend bang pip...
.venv\Scripts\python.exe -m pip install --upgrade pip
.venv\Scripts\python.exe -m pip install -r backend/requirements.txt

:VERIFY_VENV
if exist ".venv\Scripts\python.exe" goto CHECK_FRONTEND
echo [ERROR] Cai dat moi truong backend that bai. Vui long kiem tra ket noi mang.
pause
exit /b 1

:CHECK_FRONTEND
:: 4. Kiem tra thu vien Frontend
if exist "node_modules" goto LAUNCH_SERVICES

echo [INFO] Dang cai dat thu vien frontend npm install...
call npm install
if %errorlevel% equ 0 goto LAUNCH_SERVICES
echo [ERROR] Cai dat npm that bai. Vui long kiem tra ket noi mang.
pause
exit /b 1

:LAUNCH_SERVICES
:: 5. Khoi chay Backend FastAPI (Port 8000)
echo.
echo [1/3] Dang khoi dong Backend FastAPI tai cong 8000...
start "AI-Exam Backend [FastAPI:8000]" /D "%~dp0" cmd /k ".venv\Scripts\python.exe backend\main.py"

:: Cho 3 giay de Backend san sang
ping 127.0.0.1 -n 4 > nul

:: 6. Khoi chay Frontend Vite (Port 3000)
echo [2/3] Dang khoi dong Frontend Vite tai cong 3000...
start "AI-Exam Frontend [Vite:3000]" /D "%~dp0" cmd /k "npm run dev"

:: Cho 2 giay de Frontend san sang
ping 127.0.0.1 -n 3 > nul

:: 7. Tu dong mo trinh duyet
echo [3/3] Dang mo trinh duyet tai http://localhost:3000...
start http://localhost:3000

echo.
echo ================================================================================
echo   HE THONG DA KHOI CHAY THANH CONG!
echo.
echo   * Giao dien Giam sat (Frontend) : http://localhost:3000
echo   * API va Backend Service        : http://localhost:8000
echo   * Swagger API Documentation     : http://localhost:8000/docs
echo.
echo   * Hai cua so dong lenh (Backend va Frontend) dang chay song song.
echo   * De dung toan bo he thong, dong 2 cua so do hoac chay file stop.bat
echo ================================================================================
echo.
