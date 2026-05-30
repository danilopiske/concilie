@echo off
title Configurar Banco - Stack Moderno
cls

echo ============================================
echo   CONFIGURADOR DE BANCO - STACK MODERNO
echo   Financial  v2.0
echo ============================================
echo.

:MENU
echo Escolha o modo de banco de dados:
echo.
echo [1] SQLite (Single User - Recomendado)
echo [2] MySQL (Multi User)
echo [3] Cancelar
echo.
set /p opcao="Digite 1, 2 ou 3: "

if "%opcao%"=="1" goto SQLITE
if "%opcao%"=="2" goto MYSQL
if "%opcao%"=="3" goto CANCELAR
echo.
echo Opcao invalida! Tente novamente.
echo.
goto MENU

:SQLITE
echo.
echo ========================================
echo   Configurando para SQLite...
echo ========================================
copy /Y "apps\api\.env.sqlite" "apps\api\.env" >nul
if errorlevel 1 (
    echo [ERRO] Falha ao copiar configuracao SQLite
    pause
    exit /b 1
)
echo.
echo [OK] Arquivo .env configurado para SQLite
echo.
echo DATABASE_TYPE=sqlite > apps\api\.env.active
echo.
echo ========================================
echo   PROXIMOS PASSOS:
echo ========================================
echo.
echo 1. Inicie o backend:
echo    cd apps\api
echo    poetry run uvicorn app.main:app --reload
echo.
echo 2. Inicie o frontend (outro terminal):
echo    cd apps\web
echo    pnpm dev
echo.
pause
exit /b 0

:MYSQL
echo.
echo ========================================
echo   Configurando para MySQL...
echo ========================================

REM Verificar se MySQL está rodando
sc query concilie_bd | find "RUNNING" >nul
if errorlevel 1 (
    echo.
    echo [AVISO] MySQL nao detectado como servico
    echo Certifique-se de que o MySQL esta rodando!
    echo.
    pause
)

copy /Y "apps\api\.env.mysql" "apps\api\.env" >nul
if errorlevel 1 (
    echo [ERRO] Falha ao copiar configuracao MySQL
    pause
    exit /b 1
)
echo.
echo [OK] Arquivo .env configurado para MySQL
echo.
echo DATABASE_TYPE=mysql > apps\api\.env.active
echo.

REM Verificar se a senha está configurada
findstr /C:"MYSQL_PASSWORD=C0nc!l!3@123#" "apps\api\.env" >nul
if errorlevel 1 (
    echo ========================================
    echo   ATENCAO: Configuracao de Senha MySQL
    echo ========================================
    echo.
    echo O arquivo .env foi criado, mas voce precisa:
    echo.
    echo 1. Editar apps\api\.env
    echo 2. Definir MYSQL_PASSWORD=sua_senha
    echo 3. Verificar MYSQL_USER (padrao: root)
    echo.
    echo Deseja editar agora? (S/N)
    set /p editar="Digite S ou N: "
    if /i "%editar%"=="S" notepad "apps\api\.env"
    echo.
) else (
    echo ========================================
    echo   CREDENCIAIS MYSQL
    echo ========================================
    echo.
    echo [OK] Senha MySQL ja configurada
    echo Usuario: root
    echo Banco: concilie
    echo.
)
echo ========================================
echo   PROXIMOS PASSOS:
echo ========================================
echo.
echo 1. Certifique-se de que o MySQL esta rodando
echo.
echo 2. Inicie o backend:
echo    cd apps\api
echo    poetry run uvicorn app.main:app --reload
echo.
echo 3. Inicie o frontend (outro terminal):
echo    cd apps\web
echo    pnpm dev
echo.
pause
exit /b 0

:CANCELAR
echo.
echo Operacao cancelada.
pause
exit /b 0
