#!/bin/bash
# ==============================================================================
# AI EXAM CONTROL - MULTI-CAMERA SYSTEM LAUNCHER (MACOS / LINUX)
# ==============================================================================

set -e
ROOT_PATH="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT_PATH"

echo "==============================================================================="
echo "        AI EXAM CONTROL - MULTI-CAMERA SYSTEM LAUNCHER (MACOS / LINUX)         "
echo "==============================================================================="
echo ""

# 1. Tim lenh Python thich hop (python3 hoac python)
PYTHON_CMD=""
if command -v python3 >/dev/null 2>&1; then
    PYTHON_CMD="python3"
elif command -v python >/dev/null 2>&1; then
    PYTHON_CMD="python"
else
    echo "[LOI] Khong tim thay Python tren he thong!"
    echo "Vui long cai dat Python 3.10+ (qua brew install python@3.11 hoac python.org)"
    exit 1
fi

# 2. Kiem tra hoac khoi tao moi truong ao .venv
VENV_PYTHON="$ROOT_PATH/.venv/bin/python"
if [ ! -f "$VENV_PYTHON" ]; then
    echo "[THONG BAO] Chua tim thay .venv. Dang tu dong tao moi truong ao..."
    "$PYTHON_CMD" -m venv .venv
    echo "[INFO] Nang cap pip va cai dat dependencies tu backend/requirements.txt..."
    "$VENV_PYTHON" -m pip install --upgrade pip
    "$VENV_PYTHON" -m pip install -r backend/requirements.txt
    echo "[HOAN TAT] Da thiet lap xong moi truong .venv!"
    echo ""
fi

# 3. Kiem tra dependencies cua Frontend
if [ ! -d "node_modules" ]; then
    if command -v npm >/dev/null 2>&1; then
        echo "[INFO] Dang cai dat thu vien Frontend (npm install)..."
        npm install
        echo ""
    else
        echo "[LOI] Khong tim thay npm tren he thong! Vui long cai dat Node.js."
        exit 1
    fi
fi

# 4. Giai phong port 8000 va 3000 neu dang bi chiem
if command -v lsof >/dev/null 2>&1; then
    lsof -ti:8000 | xargs kill -9 2>/dev/null || true
    lsof -ti:3000 | xargs kill -9 2>/dev/null || true
fi

# 5. Khoi dong Backend AI Engine (FastAPI cong 8000)
echo "[1/2] Khoi dong Backend AI Engine (FastAPI tai cong 8000)..."
"$VENV_PYTHON" -m uvicorn main:app --app-dir backend --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!

# 6. Khoi dong Frontend Proctor Dashboard (Vite cong 3000)
echo "[2/2] Khoi dong Frontend Proctor Dashboard (Vite tai cong 3000)..."
npm run dev &
FRONTEND_PID=$!

# 7. Ham don dep khi nhan tin hieu ket thuc (Ctrl+C)
cleanup() {
    echo ""
    echo "[THONG BAO] Dang dung toan bo dich vu AI Exam..."
    kill "$BACKEND_PID" "$FRONTEND_PID" 2>/dev/null || true
    if command -v lsof >/dev/null 2>&1; then
        lsof -ti:8000 | xargs kill -9 2>/dev/null || true
        lsof -ti:3000 | xargs kill -9 2>/dev/null || true
    fi
    echo "[HOAN TAT] Da dung he thong an toan!"
    exit 0
}
trap cleanup INT TERM EXIT

# 8. Cho he thong khoi tao va mo trinh duyet
echo "[INFO] Dang khoi dong he thong va mo trinh duyet..."
sleep 3

echo ""
echo "==============================================================================="
echo "[THANH CONG] He thong da khoi dong hoan tat!"
echo " - Giao dien Giam thi: http://localhost:3000"
echo " - Backend API:         http://localhost:8000"
echo " - Trang thai Camera:   http://localhost:8000/api/camera/sources"
echo "==============================================================================="
echo "(Nhan Ctrl+C de dung he thong bat ky luc nao, hoac chay ./stop.sh)"
echo ""

if [[ "$OSTYPE" == "darwin"* ]]; then
    open "http://localhost:3000"
elif command -v xdg-open >/dev/null 2>&1; then
    xdg-open "http://localhost:3000" >/dev/null 2>&1 || true
fi

# Cho tien trinh chay nen
wait
