@echo off
title Financial Checker - Sistema de Conciliacao
echo ========================================
echo INICIANDO FINANCIAL CHECKER
echo ========================================
echo.
echo Acesse: http://localhost:8500
echo.
echo Usuario: admin
echo Senha: 1234
echo.
echo ========================================
echo.

REM Ativar ambiente virtual se existir
if exist .venv\Scripts\activate.bat (
    call .venv\Scripts\activate.bat
    echo [INFO] Usando ambiente virtual .venv
    echo.
)

REM Iniciar sistema
python main.py --mode singleuser

echo.
pause
