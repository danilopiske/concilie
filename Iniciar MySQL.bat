@echo off
title Financial  - Modo MySQL (Multi User)
cls
echo ========================================
echo    FINANCIAL  v2.0
echo    MODO: MYSQL (MULTI USER)
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

REM Verificar se MySQL está rodando
echo [1/3] Verificando MySQL...
poetry run python -c "import pymysql; conn = pymysql.connect(host='localhost', user='root', password='C0nc!l!3@123#'); print('MySQL: OK'); conn.close()" 2>nul
if errorlevel 1 (
    echo.
    echo [ERRO] MySQL nao esta rodando ou nao esta acessivel!
    echo.
    echo Verifique:
    echo   1. MySQL esta instalado?
    echo   2. MySQL esta rodando?
    echo   3. Usuario: root / Senha: C0nc!l!3@123# esta correto?
    echo.
    pause
    exit /b 1
)
echo   OK - MySQL acessivel

REM Configurar para MySQL
echo [2/3] Configurando para MySQL...
poetry run python configure_db.py mysql

REM Iniciar sistema
echo [3/3] Iniciando sistema...
echo.
echo ========================================
echo   INFORMACOES DE ACESSO
echo ========================================
echo.
echo   Modo: MYSQL (Multi User)
echo   URL: http://localhost:8500
echo.
echo   Usuario: admin
echo   Senha: admin
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
