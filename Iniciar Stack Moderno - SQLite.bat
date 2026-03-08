@echo off
title Iniciar Stack Moderno - SQLite
cls

echo ============================================
echo   FINANCIAL  v2.0
echo   STACK MODERNO - MODO SQLITE
echo ============================================
echo.
echo [!] Preparando ambiente Windows (Senior Performance Mode)...
powershell -ExecutionPolicy Bypass -File "scripts\TurboRamCleaner.ps1"
powershell -ExecutionPolicy Bypass -File "scripts\OptimizeOS.ps1"

set "API_PATH=apps\api"

REM Verificar se está configurado para SQLite
if not exist "apps\api\.env" (
    echo [ERRO] Arquivo .env nao encontrado!
    echo Execute "Configurar Stack Moderno.bat" primeiro
    pause
    exit /b 1
)

findstr /C:"DATABASE_TYPE=sqlite" "apps\api\.env" >nul
if errorlevel 1 (
    echo [AVISO] .env pode nao estar configurado para SQLite
    echo Execute "Configurar Stack Moderno.bat" para garantir
    echo.
    pause
)

echo [1/2] Verificando dependencias...
echo.

REM Verificar Poetry
poetry --version >nul 2>&1
if errorlevel 1 (
    echo [ERRO] Poetry nao encontrado!
    echo Instale com: pip install poetry
    pause
    exit /b 1
)
echo [OK] Poetry encontrado

REM Verificar pnpm
pnpm --version >nul 2>&1
if errorlevel 1 (
    echo [ERRO] pnpm nao encontrado!
    echo Instale com: npm install -g pnpm
    pause
    exit /b 1
)
echo [OK] pnpm encontrado

echo.
echo ========================================
echo   INICIANDO SERVICOS...
echo ========================================
echo.
echo Backend FastAPI: http://localhost:8000
echo Frontend Next.js: http://localhost:3000
echo API Docs: http://localhost:8000/docs
echo.
echo [AVISO] Abra 2 terminais separados:
echo.
echo Terminal 1 - Backend:
echo   cd apps\api
echo   poetry run uvicorn app.main:app --reload
echo.
echo Terminal 2 - Frontend:
echo   cd apps\web
echo   pnpm dev
echo.
echo Pressione qualquer tecla para abrir os terminais...
echo [!] Limpando processos antigos (Python/Node)...
taskkill /f /im python.exe /t >nul 2>&1
taskkill /f /im node.exe /t >nul 2>&1
timeout /t 2 /nobreak >nul

pause >nul

REM Abrir terminal para backend
echo [>] Iniciando Backend (SQLite)...
start "Financial - Backend (SQLite)" cmd /k "cd /d %CD%\apps\api && set PYTHONOPTIMIZE=1 && poetry run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 --reload-dir app --reload-exclude 'node_modules/*,.next/*,dist/*'"

REM Aguardar 5 segundos
timeout /t 5 /nobreak >nul

REM Abrir terminal para frontend
echo [>] Iniciando Frontend...
start "Financial - Frontend" cmd /k "cd /d %CD%\apps\web && pnpm dev --turbo"

echo.
echo ========================================
echo   Servicos iniciados!
echo ========================================
echo.
echo Backend e Frontend estao rodando em terminais separados.
echo Feche este terminal com seguranca.
echo.
pause
exit /b 0
