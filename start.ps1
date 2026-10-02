# ==============================================================================
# AI EXAM CONTROL - POWERSHELL LAUNCHER (MULTI-CAMERA)
# ==============================================================================

$RootPath = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $RootPath

Write-Host "===============================================================================" -ForegroundColor Cyan
Write-Host "                AI EXAM CONTROL - MULTI-CAMERA SYSTEM LAUNCHER                 " -ForegroundColor Cyan
Write-Host "===============================================================================" -ForegroundColor Cyan
Write-Host ""

$PythonExe = Join-Path $RootPath ".venv\Scripts\python.exe"
if (-not (Test-Path $PythonExe)) {
    Write-Host "[THONG BAO] Chua tim thay .venv tai thu muc goc. Dang tu dong tao moi..." -ForegroundColor Yellow
    $SystemPython = (Get-Command python.exe -ErrorAction SilentlyContinue)
    if (-not $SystemPython) {
        Write-Host "[LOI] Khong tim thay Python tren he thong!" -ForegroundColor Red
        Write-Host "Vui long cai dat Python 3.10+ va tich Add to PATH tu https://www.python.org/downloads/" -ForegroundColor Yellow
        exit 1
    }
    python -m venv .venv
    & $PythonExe -m pip install --upgrade pip
    & $PythonExe -m pip install -r backend/requirements.txt
    Write-Host "[HOAN TAT] Da khoi tao xong .venv!" -ForegroundColor Green
    Write-Host ""
}

if (-not (Test-Path (Join-Path $RootPath "node_modules"))) {
    $NpmCmd = (Get-Command npm.cmd -ErrorAction SilentlyContinue)
    if ($NpmCmd) {
        Write-Host "[INFO] Dang cai dat thu vien Frontend (npm install)..." -ForegroundColor Yellow
        npm install
        Write-Host ""
    }
}

Write-Host "[1/3] Khoi dong Backend AI Engine (FastAPI tren cong 8000)..." -ForegroundColor Yellow
Start-Process -FilePath "cmd.exe" -ArgumentList "/k chcp 65001 >nul && cd /d `"$RootPath`" && `"$PythonExe`" -m uvicorn main:app --app-dir backend --host 0.0.0.0 --port 8000"

Write-Host "[2/3] Khoi dong Frontend Proctor Dashboard (Vite tren cong 3000)..." -ForegroundColor Yellow
Start-Process -FilePath "cmd.exe" -ArgumentList "/k chcp 65001 >nul && cd /d `"$RootPath`" && npm run dev"

Write-Host "[3/3] Cho he thong khoi tao trong 3 giay..." -ForegroundColor Yellow
Start-Sleep -Seconds 3

Write-Host ""
Write-Host "===============================================================================" -ForegroundColor Green
Write-Host "[THANH CONG] He thong da khoi dong!" -ForegroundColor Green
Write-Host " - Giao dien Dashboard: http://localhost:3000" -ForegroundColor White
Write-Host " - Backend API:         http://localhost:8000" -ForegroundColor White
Write-Host " - Kiem tra camera:     http://localhost:8000/api/camera/sources" -ForegroundColor White
Write-Host "===============================================================================" -ForegroundColor Green
Write-Host ""

Start-Process "http://localhost:3000"
Write-Host "Dang mo trinh duyet..." -ForegroundColor Cyan
Write-Host "(De dung he thong bat ky luc nao, hay chay ./stop.ps1 hoac stop.bat)" -ForegroundColor Gray
