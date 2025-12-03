@echo off
title Financial Checker - Instalacao
echo ========================================
echo INSTALACAO DO FINANCIAL CHECKER
echo ========================================
echo.
echo Este script vai:
echo   1. Criar ambiente virtual Python
echo   2. Ativar o ambiente
echo   3. Instalar dependencias
echo.
echo ========================================
echo.

REM Criar ambiente virtual
echo [1/3] Criando ambiente virtual...
python -m venv .venv
if errorlevel 1 (
    echo.
    echo ERRO: Nao foi possivel criar ambiente virtual
    echo Verifique se Python esta instalado corretamente
    pause
    exit /b 1
)
echo   OK Ambiente .venv criado
echo.

REM Ativar ambiente virtual e instalar
echo [2/3] Ativando ambiente e instalando...
call .venv\Scripts\activate.bat
if errorlevel 1 (
    echo.
    echo ERRO: Nao foi possivel ativar ambiente virtual
    pause
    exit /b 1
)
echo   OK Ambiente ativado
echo.

REM Executar instalacao
echo [3/3] Executando instalacao...
echo.
python install.py

echo.
echo ========================================
echo.
pause
