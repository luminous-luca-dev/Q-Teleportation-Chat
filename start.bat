@echo off
chcp 65001 > nul
echo ========================================================
echo   量子テレポーテーション・チャットシミュレータ 起動
echo ========================================================

echo [1/2] バックエンド (FastAPI / Qiskit) を起動中...
start "Quantum Backend (Port 8000)" cmd /k "cd /d %~dp0backend && python -X utf8 -m uvicorn main:app --reload --host 0.0.0.0 --port 8000"

echo [2/2] フロントエンド (Next.js) を起動中...
start "Quantum Frontend (Port 3000)" cmd /k "cd /d %~dp0frontend && npm run dev"

echo.
echo アプリケーションを起動しました:
echo   - フロントエンド: http://localhost:3000
echo   - バックエンド API: http://localhost:8000/docs
echo ========================================================
pause
