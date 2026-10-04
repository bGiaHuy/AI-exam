#!/bin/bash
# ==============================================================================
# AI EXAM CONTROL - DUNG TOAN BO DICH VU (MACOS / LINUX)
# ==============================================================================

echo "==============================================================================="
echo "                AI EXAM CONTROL - DUNG DICH VU (MACOS / LINUX)                 "
echo "==============================================================================="
echo ""

echo "[1/2] Dang dung Backend (Port 8000)..."
if command -v lsof >/dev/null 2>&1; then
    lsof -ti:8000 | xargs kill -9 2>/dev/null || true
fi
pkill -f "uvicorn main:app" 2>/dev/null || true

echo "[2/2] Dang dung Frontend (Port 3000)..."
if command -v lsof >/dev/null 2>&1; then
    lsof -ti:3000 | xargs kill -9 2>/dev/null || true
fi
pkill -f "vite" 2>/dev/null || true

echo ""
echo "==============================================================================="
echo "[HOAN TAT] He thong Backend va Frontend da duoc dung sach se!"
echo "==============================================================================="
echo ""
