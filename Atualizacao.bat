@echo off
title Financial  - Atualizacao do Sistema
echo ========================================
echo ATUALIZACAO DO FINANCIAL 
echo ========================================
echo.
echo Este script vai:
echo   1. Atualizar codigo via Git (se disponivel)
echo   2. Atualizar dependencias Python
echo.
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

REM Atualizar código via Git
echo [1/2] Atualizando codigo via Git...
git --version >nul 2>&1
if errorlevel 1 (
    echo   [AVISO] Git nao encontrado - pulando atualizacao de codigo
) else (
    git pull
    if errorlevel 1 (
        echo   [AVISO] Nao foi possivel atualizar via Git
    ) else (
        echo   OK Codigo atualizado
    )
)
echo.

REM Atualizar dependências
echo [2/2] Atualizando dependencias Python...
poetry install --only main
if errorlevel 1 (
    echo.
    echo [ERRO] Falha na atualizacao de dependencias
    pause
    exit /b 1
)

echo.
echo ========================================
echo ATUALIZACAO CONCLUIDA COM SUCESSO!
echo ========================================
echo.
echo Execute "Iniciar Sistema.bat" para reiniciar o sistema
echo.
pause
