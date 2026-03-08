@echo off
title Financial  - Instalacao via Poetry
echo ========================================
echo INSTALACAO DO FINANCIAL 
echo Sistema de Conciliacao Financeira v2.0
echo ========================================
echo.
echo Este script vai:
echo   1. Verificar Poetry
echo   2. Instalar dependencias
echo   3. Configurar banco de dados
echo.
echo ========================================
echo.

REM Verificar se Poetry está instalado
echo [1/3] Verificando Poetry...
poetry --version >nul 2>&1
if errorlevel 1 (
    echo.
    echo [ERRO] Poetry nao encontrado!
    echo.
    echo Por favor, instale Poetry primeiro:
    echo   https://python-poetry.org/docs/#installation
    echo.
    echo Ou execute no PowerShell:
    echo   pip install poetry
    echo.
    pause
    exit /b 1
)
echo   OK Poetry encontrado
echo.

REM Instalar dependências
echo [2/3] Instalando dependencias...
echo (Isso pode levar alguns minutos...)
echo.
poetry install --only main
if errorlevel 1 (
    echo.
    echo [ERRO] Falha na instalacao de dependencias
    echo.
    pause
    exit /b 1
)
echo.
echo   OK Dependencias instaladas
echo.

REM Configurar banco de dados
echo [3/3] Configurando banco de dados...
echo.
poetry run python configure_db.py
if errorlevel 1 (
    echo.
    echo [AVISO] Configuracao do banco pode precisar de ajustes manuais
    echo.
)

echo.
echo ========================================
echo INSTALACAO CONCLUIDA COM SUCESSO!
echo ========================================
echo.
echo Proximos passos:
echo   1. Execute "Configurar Banco.bat" se necessario
echo   2. Execute "Iniciar Sistema.bat" para iniciar
echo.
echo ========================================
echo.
pause
