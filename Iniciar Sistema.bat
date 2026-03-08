@echo off
title Financial  - Sistema de Conciliacao v2.0
cls
echo ========================================
echo    FINANCIAL  v2.0
echo    Sistema de Conciliacao Financeira
echo ========================================
echo.

REM Verificar Poetry
poetry --version >nul 2>&1
if errorlevel 1 (
    echo [ERRO] Poetry nao encontrado!
    echo.
    echo Execute "Instalar.bat" primeiro
    echo.
    pause
    exit /b 1
)

echo [INFO] Iniciando sistema...
echo.
echo ========================================
echo   INFORMACOES DE ACESSO
echo ========================================
echo.
echo   URL: http://localhost:8500
echo.
echo   Usuario: admin
echo   Senha: 1234
echo.
echo ========================================
echo.
echo Pressione Ctrl+C para encerrar o sistema
echo.
echo ========================================
echo.

REM Iniciar aplicação via Poetry
poetry run python main.py --mode singleuser

if errorlevel 1 (
    echo.
    echo ========================================
    echo [ERRO] Sistema encerrado com erro
    echo ========================================
    echo.
    pause
)
