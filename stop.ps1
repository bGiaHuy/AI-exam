# ==============================================================================
# AI EXAM CONTROL - POWERSHELL STOPPER
# ==============================================================================

Write-Host "===============================================================================" -ForegroundColor Cyan
Write-Host "                AI EXAM CONTROL - DUNG DICH VU                                " -ForegroundColor Cyan
Write-Host "===============================================================================" -ForegroundColor Cyan
Write-Host ""

function Stop-PortProcess([int]$Port) {
    $connections = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue
    if ($connections) {
        foreach ($conn in $connections) {
            $pidToKill = $conn.OwningProcess
            if ($pidToKill -gt 0) {
                Write-Host "Dung tien trinh PID $pidToKill tren cong $Port..." -ForegroundColor Yellow
                Stop-Process -Id $pidToKill -Force -ErrorAction SilentlyContinue
            }
        }
    } else {
        Write-Host "Khong co tien trinh nao dang lang nghe tren cong $Port." -ForegroundColor Gray
    }
}

Stop-PortProcess -Port 8000
Stop-PortProcess -Port 3000

Write-Host ""
Write-Host "===============================================================================" -ForegroundColor Green
Write-Host "[HOAN TAT] He thong da duoc dung thanh cong!" -ForegroundColor Green
Write-Host "===============================================================================" -ForegroundColor Green
