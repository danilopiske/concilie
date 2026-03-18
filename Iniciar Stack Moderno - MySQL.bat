@echo off
title Iniciar Stack Moderno - MySQL
cls

echo ============================================
echo   FINANCIAL  v2.0
echo   STACK MODERNO - MODO MYSQL
echo ============================================
echo.

echo [!] Preparando ambiente Windows (Senior Performance Mode)...
powershell -ExecutionPolicy Bypass -File "%~dp0scripts\TurboRamCleaner.ps1"
powershell -ExecutionPolicy Bypass -File "%~dp0scripts\OptimizeOS.ps1"

set "API_PATH=apps\api"

REM Verificar se está configurado para MySQL
if not exist "apps\api\.env" (
    echo [ERRO] Arquivo .env nao encontrado!
    echo Execute "Configurar Stack Moderno.bat" primeiro
    pause
    exit /b 1
)

findstr /C:"DATABASE_TYPE=mysql" "apps\api\.env" >nul
if errorlevel 1 (
    echo [AVISO] .env pode nao estar configurado para MySQL
    echo Execute "Configurar Stack Moderno.bat" para garantir
    echo.
    pause
)

echo [1/3] Verificando MySQL...
sc query concilie_bd | find "RUNNING" >nul
if errorlevel 1 (
    echo [ERRO] Servico MySQL (concilie_bd) nao encontrado ou parado!
    echo Use: net start concilie_bd
    pause
    exit /b 1
)
echo [OK] MySQL rodando

echo.
echo [2/3] Verificando dependencias...

REM Verificar Poetry via where
where poetry >nul 2>&1
if errorlevel 1 (
    echo [ERRO] Poetry nao encontrado no PATH!
) else (
    echo [OK] Poetry encontrado
)

REM Verificar pnpm via where
where pnpm >nul 2>&1
if errorlevel 1 (
    echo [ERRO] pnpm nao encontrado no PATH!
) else (
    echo [OK] pnpm encontrado
)

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

echo.
echo [>] Iniciando Backend...
start "Financial - Backend (MySQL)" cmd /k "cd /d \"%~dp0apps\api\" && set PYTHONOPTIMIZE=1 && poetry run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 --reload-dir app"

echo [>] Aguardando 3 segundos...
timeout /t 3 /nobreak >nul

echo [>] Iniciando Frontend...
start "Financial - Frontend" cmd /k "cd /d \"%~dp0apps\web\" && pnpm dev --turbo"

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
