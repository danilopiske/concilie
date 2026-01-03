@echo off
title Financial Checker - Configuracao de Banco
echo ========================================
echo CONFIGURACAO DE BANCO DE DADOS
echo ========================================
echo.
echo Escolha o tipo de banco:
echo   [1] MySQL (Desenvolvimento)
echo   [2] SQLite (Distribuicao)
echo   [3] Ver Status Atual
echo   [0] Sair
echo.
echo ========================================
echo.

set /p opcao="Digite sua opcao: "

if "%opcao%"=="1" goto mysql
if "%opcao%"=="2" goto sqlite
if "%opcao%"=="3" goto status
if "%opcao%"=="0" goto fim
goto invalido

:mysql
echo.
echo Configurando para MySQL...
python configure_db.py mysql
goto fim

:sqlite
echo.
echo Configurando para SQLite...
python configure_db.py sqlite
goto fim

:status
echo.
python configure_db.py status
goto fim

:invalido
echo.
echo Opcao invalida!
goto fim

:fim
echo.
pause
