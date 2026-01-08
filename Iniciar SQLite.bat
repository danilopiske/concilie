@echo off
title Financial Checker - Modo SQLite (Single User)
cls
echo ========================================
echo    FINANCIAL CHECKER v2.0
echo    MODO: SQLITE (SINGLE USER)
echo ========================================
echo.

REM Verificar Poetry
poetry --version >nul 2>&1
if errorlevel 1 (
    echo [ERRO] Poetry nao encontrado!
    echo Execute "Instalar.bat" primeiro
    pause
    exit /b 1
)

REM Configurar para SQLite
echo [1/2] Configurando para SQLite...
poetry run python configure_db.py sqlite

REM Iniciar sistema
echo [2/2] Iniciando sistema...
echo.
echo ========================================
echo   INFORMACOES DE ACESSO
echo ========================================
echo.
echo   Modo: SQLITE (Single User)
echo   URL: http://localhost:8500
echo.
echo   Usuario: admin
echo   Senha: 1234
echo.
echo ========================================
echo.
echo Pressione Ctrl+C para encerrar
echo.

poetry run python main.py

if errorlevel 1 (
    echo.
    echo ========================================
    echo [ERRO] Sistema encerrado com erro
    echo ========================================
    pause
)
