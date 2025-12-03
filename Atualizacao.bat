@echo off
title Financial Checker - Instalacao Kaleido
echo ========================================
echo INSTALACAO DO KALEIDO
echo ========================================
echo.
echo Este script vai instalar o pacote Kaleido
echo necessario para geracao de graficos
echo.
echo ========================================
echo.

REM Ativar ambiente virtual
echo Ativando ambiente virtual...
call .venv\Scripts\activate.bat
if errorlevel 1 (
    echo.
    echo ERRO: Nao foi possivel ativar ambiente virtual
    echo Execute primeiro o Instalar.bat
    pause
    exit /b 1
)
echo   OK Ambiente ativado
echo.

REM Instalar kaleido
echo Instalando kaleido...
pip install kaleido
if errorlevel 1 (
    echo.
    echo ERRO: Nao foi possivel instalar kaleido
    pause
    exit /b 1
)
echo.
echo   OK Kaleido instalado com sucesso
echo.

echo ========================================
echo INSTALACAO CONCLUIDA
echo ========================================
echo.
pause
