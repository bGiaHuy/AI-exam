@echo off
chcp 65001 > nul
setlocal enabledelayedexpansion

title AI Exam Control - Automated Proctoring System
cd /d "%~dp0"

echo ================================================================================
echo           HỆ THỐNG GIÁM SÁT THI CỬ THÔNG MINH - AI EXAM CONTROL
echo ================================================================================
echo.

:: 1. Kiểm tra Python
where python >nul 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] Không tìm thấy Python trên máy tính!
    echo Vui lòng cài đặt Python (>= 3.10) và tích chọn "Add Python to PATH".
    echo Tải tại: https://www.python.org/downloads/
    pause
    exit /b 1
)

:: 2. Kiểm tra Node.js
where node >nul 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] Không tìm thấy Node.js trên máy tính!
    echo Vui lòng cài đặt Node.js (>= 18) để chạy giao diện Frontend.
    echo Tải tại: https://nodejs.org/
    pause
    exit /b 1
)

:: 3. Kiểm tra môi trường ảo Python (.venv)
if not exist ".venv\Scripts\python.exe" (
    echo [INFO] Đang khởi tạo môi trường ảo Python (.venv)...
    where uv >nul 2>nul
    if %errorlevel% equ 0 (
        uv venv .venv
        echo [INFO] Đang cài đặt thư viện backend bằng uv...
        uv pip install -r backend/requirements.txt --python .venv\Scripts\python.exe
    ) else (
        python -m venv .venv
        echo [INFO] Đang cài đặt thư viện backend bằng pip (có thể mất vài phút)...
        .venv\Scripts\python.exe -m pip install --upgrade pip
        .venv\Scripts\python.exe -m pip install -r backend/requirements.txt
    )
    if %errorlevel% neq 0 (
        echo [ERROR] Cài đặt thư viện backend thất bại. Vui lòng kiểm tra kết nối mạng.
        pause
        exit /b 1
    )
)

:: 4. Kiểm tra thư viện Frontend (node_modules)
if not exist "node_modules" (
    echo [INFO] Đang cài đặt thư viện frontend (npm install)...
    call npm install
    if %errorlevel% neq 0 (
        echo [ERROR] Cài đặt npm thất bại. Vui lòng kiểm tra kết nối mạng.
        pause
        exit /b 1
    )
)

:: 5. Khởi chạy Backend FastAPI (Cổng 8000)
echo.
echo [1/3] Đang khởi động Backend FastAPI (Port 8000)...
start "AI-Exam Backend [FastAPI:8000]" cmd /k "cd /d ""%~dp0"" && title AI-Exam Backend [FastAPI:8000] && .venv\Scripts\python.exe backend/main.py"

:: Chờ 3 giây để Backend sẵn sàng
timeout /t 3 /nobreak > nul

:: 6. Khởi chạy Frontend Vite (Cổng 3000)
echo [2/3] Đang khởi động Frontend Vite (Port 3000)...
start "AI-Exam Frontend [Vite:3000]" cmd /k "cd /d ""%~dp0"" && title AI-Exam Frontend [Vite:3000] && npm run dev"

:: Chờ 2 giây để Frontend sẵn sàng
timeout /t 2 /nobreak > nul

:: 7. Tự động mở trình duyệt Web
echo [3/3] Đang mở trình duyệt tại http://localhost:3000...
start http://localhost:3000

echo.
echo ================================================================================
echo   HỆ THỐNG ĐÃ KHỞI CHẠY THÀNH CÔNG!
echo.
echo   * Giao diện Giám sát (Frontend) : http://localhost:3000
echo   * API & Backend Service         : http://localhost:8000
echo   * Swagger API Documentation     : http://localhost:8000/docs
echo.
echo   * Hai cửa sổ dòng lệnh (Backend & Frontend) đang chạy song song.
echo   * Để dừng toàn bộ hệ thống, bạn có thể đóng 2 cửa sổ đó hoặc chạy file stop.bat
echo ================================================================================
echo.

pause
