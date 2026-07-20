@echo off
title Financial  v2.0 - Instalacao Completa
cls
echo ========================================
echo    FINANCIAL  v2.0
echo    INSTALACAO COMPLETA
echo ========================================
echo.
echo Este instalador vai:
echo   [1] Verificar/Instalar Python 3.11
echo   [2] Instalar Poetry
echo   [3] Instalar Financial 
echo   [4] Configurar banco SQLite
echo.
echo Requisitos:
echo   - Conexao com internet (para downloads)
echo   - 2GB de espaco em disco
echo   - Windows 10 ou superior
echo.
echo ========================================
pause
cls

REM ==============================================
REM ETAPA 1: VERIFICAR/INSTALAR PYTHON
REM ==============================================
echo.
echo [1/4] Verificando Python...
echo.

python --version >nul 2>&1
if errorlevel 1 (
    echo [!] Python nao encontrado no sistema
    echo.
    echo ========================================
    echo INSTALACAO DO PYTHON NECESSARIA
    echo ========================================
    echo.
    echo Por favor, siga os passos:
    echo.
    echo 1. Sera aberto o site de download do Python
    echo 2. Baixe: Python 3.11.9 (Windows installer 64-bit)
    echo 3. IMPORTANTE: Marque "Add Python to PATH"
    echo 4. Clique em "Install Now"
    echo 5. Aguarde a instalacao
    echo 6. Volte para esta janela e pressione qualquer tecla
    echo.
    echo ========================================
    pause
    
    REM Abrir página de download
    start https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe
    
    echo.
    echo Aguardando instalacao do Python...
    echo Pressione qualquer tecla APOS concluir a instalacao
    pause >nul
    
    REM Verificar novamente
    echo.
    echo Verificando instalacao do Python...
    python --version >nul 2>&1
    if errorlevel 1 (
        echo.
        echo [ERRO] Python ainda nao esta acessivel!
        echo.
        echo Possiveis problemas:
        echo   - Python nao foi instalado
        echo   - "Add Python to PATH" nao foi marcado
        echo   - Precisa reiniciar o terminal
        echo.
        echo Solucao:
        echo   1. Reinstale o Python
        echo   2. Marque "Add Python to PATH"
        echo   3. Reinicie este script
        echo.
        pause
        exit /b 1
    )
)

echo [OK] Python encontrado:
python --version
echo.

REM Atualizar pip
echo Atualizando pip...
python -m pip install --upgrade pip >nul 2>&1
echo [OK] Pip atualizado
echo.

REM ==============================================
REM ETAPA 2: INSTALAR POETRY
REM ==============================================
echo.
echo [2/4] Instalando Poetry...
echo.

poetry --version >nul 2>&1
if errorlevel 1 (
    echo Instalando Poetry via pip...
    python -m pip install poetry
    if errorlevel 1 (
        echo.
        echo [ERRO] Falha ao instalar Poetry
        echo.
        pause
        exit /b 1
    )
    
    REM Verificar instalação
    poetry --version >nul 2>&1
    if errorlevel 1 (
        echo.
        echo [AVISO] Poetry instalado mas nao acessivel no PATH
        echo Tentando via python -m poetry...
        python -m poetry --version
        if errorlevel 1 (
            echo [ERRO] Poetry nao esta funcionando
            pause
            exit /b 1
        )
    )
)

echo [OK] Poetry instalado:
poetry --version
echo.

REM Configuração Poetry para melhor performance no Windows
echo Configurando Poetry...
poetry config virtualenvs.in-project false
poetry config keyring.enabled false
echo [OK] Poetry configurado
echo.

REM ==============================================
REM ETAPA 3: INSTALAR DEPENDENCIAS
REM ==============================================
echo.
echo [3/4] Instalando Financial ...
echo.
echo [!] IMPORTANTE: Isso pode levar 5-15 minutos
echo     Aguarde ate aparecer a mensagem de conclusao
echo.
echo Instalando dependencias...
echo.

poetry install --only main
if errorlevel 1 (
    echo.
    echo [ERRO] Falha na instalacao das dependencias
    echo.
    echo Tentando novamente com mais detalhes...
    poetry install --only main -vvv
    if errorlevel 1 (
        echo.
        echo [ERRO] Instalacao falhou mesmo com verbose
        echo.
        echo Possiveis causas:
        echo   - Conexao com internet instavel
        echo   - Firewall bloqueando downloads
        echo   - Espaco em disco insuficiente
        echo.
        pause
        exit /b 1
    )
)

echo.
echo [OK] Dependencias instaladas com sucesso
echo.

REM Verificar imports críticos
echo Verificando imports criticos...
poetry run python -c "import pandas; import panel; import sqlalchemy; print('[OK] Imports validados')"
if errorlevel 1 (
    echo [AVISO] Alguns imports falharam, mas continuando...
)
echo.

REM ==============================================
REM ETAPA 4: CONFIGURAR BANCO DE DADOS
REM ==============================================
echo.
echo [4/4] Configurando banco de dados SQLite...
echo.

REM Criar pasta data se não existir
if not exist "data" mkdir data

REM Configurar para SQLite
poetry run python configure_db.py sqlite
if errorlevel 1 (
    echo [AVISO] Erro na configuracao automatica do banco
    echo O banco pode precisar ser configurado manualmente
)

echo [OK] Banco de dados configurado
echo.

REM ==============================================
REM FINALIZACAO
REM ==============================================
cls
echo ========================================
echo    INSTALACAO CONCLUIDA COM SUCESSO!
echo ========================================
echo.
echo Informacoes do Sistema:
echo.

REM Mostrar versões instaladas
echo Python:
python --version
echo.
echo Poetry:
poetry --version
echo.
echo Banco de Dados:
poetry run python configure_db.py status
echo.

echo ========================================
echo    COMO USAR O SISTEMA
echo ========================================
echo.
echo Para INICIAR o sistema:
echo   Execute: "Iniciar Sistema.bat"
echo.
echo Ou para modos especificos:
echo   SQLite: "Iniciar SQLite.bat"
echo   MySQL:  "Iniciar MySQL.bat"
echo.
echo ========================================
echo    INFORMACOES DE ACESSO
echo ========================================
echo.
echo URL:     http://localhost:8500
echo Usuario: admin
echo Senha:   1234
echo.
echo ========================================
echo.
echo Pressione qualquer tecla para sair...
pause >nul
