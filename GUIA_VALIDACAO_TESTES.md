# 🧪 GUIA DE VALIDAÇÃO E TESTES - Financial Checker v2.0

## 📋 Índice
1. [Testar na Máquina de Desenvolvimento](#testar-desenvolvimento)
2. [Testar em Máquina Limpa (VM)](#testar-vm)
3. [Validação dos Dois Modos](#validação-modos)
4. [Troubleshooting](#troubleshooting)

---

## 🖥️ 1. Testar na Máquina de Desenvolvimento {#testar-desenvolvimento}

### ✅ Modo 1: SQLite (Single User) - RECOMENDADO PARA DISTRIBUIÇÃO

**Características:**
- ✅ Não precisa de MySQL rodando
- ✅ Banco em arquivo único: `data/concilie.db`
- ✅ Ideal para instalação em clientes
- ✅ Zero configuração de servidor

**Como iniciar:**

#### Opção A: Script Dedicado (NOVO)
```batch
Iniciar SQLite.bat
```

#### Opção B: Script Genérico
```batch
# 1. Configurar para SQLite
Configurar Banco.bat
# Escolha opção [2] SQLite

# 2. Iniciar
Iniciar Sistema.bat
```

#### Opção C: Manual (via Poetry)
```bash
# Configurar
poetry run python configure_db.py sqlite

# Iniciar
poetry run python main.py
```

**Validação:**
1. ✅ Sistema deve iniciar sem erros
2. ✅ Deve aparecer: "Usando SQLite"
3. ✅ Acessar http://localhost:8500
4. ✅ Login: admin / 1234

---

### ✅ Modo 2: MySQL (Multi User) - DESENVOLVIMENTO/PRODUÇÃO

**Características:**
- ⚠️ Requer MySQL rodando
- ✅ Performance superior para grandes volumes
- ✅ Suporte multi-usuário robusto
- ✅ Ideal para servidor/desenvolvimento

**Pré-requisitos:**
```batch
# Verificar se MySQL está rodando
services.msc
# Procurar: MySQL80 (ou MySQL57)
# Status deve estar: Em execução
```

**Como iniciar:**

#### Opção A: Script Dedicado (NOVO)
```batch
Iniciar MySQL.bat
```

#### Opção B: Script Genérico
```batch
# 1. Configurar para MySQL
Configurar Banco.bat
# Escolha opção [1] MySQL

# 2. Iniciar
Iniciar Sistema.bat
```

#### Opção C: Manual (via Poetry)
```bash
# Configurar
poetry run python configure_db.py mysql

# Iniciar
poetry run python main.py
```

**Validação:**
1. ✅ Sistema deve iniciar sem erros
2. ✅ Deve aparecer: "Usando MySQL"
3. ✅ Acessar http://localhost:8500
4. ✅ Login: admin / 1234

---

## 🔄 Alternando Entre Modos

### Ver Modo Atual
```batch
Configurar Banco.bat
# Escolha opção [3] Ver Status Atual
```

Ou:
```bash
poetry run python configure_db.py status
```

### Trocar de Modo
```batch
# De SQLite para MySQL
Iniciar MySQL.bat

# De MySQL para SQLite
Iniciar SQLite.bat
```

---

## 🆕 2. Testar em Máquina Limpa (VM) {#testar-vm}

### 🎯 Opção 1: Máquina Virtual (Recomendado para Teste Completo)

#### Preparação da VM

**Software Necessário:**
- VirtualBox: https://www.virtualbox.org/wiki/Downloads
- Windows 10/11 ISO: https://www.microsoft.com/pt-br/software-download/windows10

**Configuração VM:**
1. Criar nova VM no VirtualBox
2. Configurações:
   - RAM: 4GB mínimo (8GB recomendado)
   - Disco: 50GB
   - Rede: NAT ou Bridge
3. Instalar Windows
4. Desabilitar Windows Defender (temporário, para teste)

#### Teste 1: Instalação Completa (Python + Poetry + Sistema)

**1. Preparar Pacote de Distribuição:**

Na máquina de desenvolvimento:
```batch
# Criar pasta de distribuição
mkdir distribuicao
mkdir distribuicao\Financial_Checker_v2.0

# Copiar arquivos necessários
xcopy /E /I /H /Y "D:\Financial Checker base\Financial_P" "D:\distribuicao\Financial_Checker_v2.0"

# Remover arquivos desnecessários
cd distribuicao\Financial_Checker_v2.0
rmdir /s /q __pycache__
rmdir /s /q .venv
rmdir /s /q dev_tools
del /f /q debug.txt
del /f /q .db_config

# Criar README para instalação
```

**2. Criar Instalador Completo para Distribuição:**

Crie o arquivo: `distribuicao\Financial_Checker_v2.0\INSTALAR_COMPLETO.bat`
```batch
@echo off
title Financial Checker v2.0 - Instalacao Completa
cls
echo ========================================
echo    FINANCIAL CHECKER v2.0
echo    INSTALACAO COMPLETA
echo ========================================
echo.
echo Este instalador vai:
echo   [1] Baixar e instalar Python 3.11
echo   [2] Instalar Poetry
echo   [3] Instalar Financial Checker
echo   [4] Configurar banco SQLite
echo.
echo Requisitos:
echo   - Conexao com internet
echo   - 2GB de espaco em disco
echo   - Windows 10 ou superior
echo.
pause
echo.

REM Verificar se Python está instalado
python --version >nul 2>&1
if errorlevel 1 (
    echo [1/4] Python nao encontrado. Instalando...
    echo.
    echo [INFO] Baixando Python 3.11...
    echo Por favor, baixe Python de: https://www.python.org/downloads/
    echo.
    echo Importante:
    echo   - Marque "Add Python to PATH"
    echo   - Instale para todos os usuarios
    echo.
    echo Pressione qualquer tecla APOS instalar Python...
    pause
    
    REM Verificar novamente
    python --version >nul 2>&1
    if errorlevel 1 (
        echo [ERRO] Python ainda nao encontrado!
        echo Por favor, instale Python e tente novamente.
        pause
        exit /b 1
    )
)
echo [1/4] Python encontrado
python --version
echo.

REM Instalar Poetry
echo [2/4] Instalando Poetry...
pip install poetry
if errorlevel 1 (
    echo [ERRO] Falha ao instalar Poetry
    pause
    exit /b 1
)
echo   OK - Poetry instalado
echo.

REM Instalar dependências
echo [3/4] Instalando Financial Checker...
echo (Isso pode levar alguns minutos...)
echo.
poetry install --only main
if errorlevel 1 (
    echo [ERRO] Falha na instalacao
    pause
    exit /b 1
)
echo   OK - Dependencias instaladas
echo.

REM Configurar SQLite
echo [4/4] Configurando banco de dados SQLite...
poetry run python configure_db.py sqlite
if errorlevel 1 (
    echo [AVISO] Configuracao do banco pode precisar de ajustes
)
echo.

echo ========================================
echo   INSTALACAO CONCLUIDA!
echo ========================================
echo.
echo Para iniciar o sistema:
echo   Execute: "Iniciar Sistema.bat"
echo.
echo Acesso:
echo   URL: http://localhost:8500
echo   Usuario: admin
echo   Senha: 1234
echo.
pause
```

**3. Na VM - Instalar:**

1. Copiar pasta `Financial_Checker_v2.0` para VM (via pendrive ou pasta compartilhada)
2. Executar `INSTALAR_COMPLETO.bat`
3. Aguardar instalação (10-20 minutos)
4. Executar `Iniciar Sistema.bat`

**4. Validação na VM:**
```
✅ Python instalado?
✅ Poetry instalado?
✅ Dependências instaladas?
✅ SQLite configurado?
✅ Sistema inicia sem erros?
✅ Interface acessível em http://localhost:8500?
✅ Login funciona?
✅ Funcionalidades principais funcionam?
```

---

#### Teste 2: Instalação com Python Pré-instalado

**Se a VM já tiver Python:**

1. Copiar projeto para VM
2. Executar:
```batch
Instalar.bat
Iniciar Sistema.bat
```

**Validação:**
```
✅ Poetry instala corretamente?
✅ Dependências instalam sem erros?
✅ Sistema inicia?
```

---

### 🎯 Opção 2: Máquina de Teste Física

**Se você tiver acesso a outro computador:**

1. Copiar pasta do projeto
2. Seguir mesmo processo da VM
3. Testar instalação limpa

---

### 🎯 Opção 3: Windows Sandbox (Mais Rápido)

**Requer: Windows 10/11 Pro ou Enterprise**

**1. Habilitar Windows Sandbox:**
```
Painel de Controle > Programas > Ativar recursos do Windows
Marcar: Windows Sandbox
Reiniciar
```

**2. Criar configuração do Sandbox:**

Arquivo: `FinancialChecker_Sandbox.wsb`
```xml
<Configuration>
  <MappedFolders>
    <MappedFolder>
      <HostFolder>D:\distribuicao\Financial_Checker_v2.0</HostFolder>
      <ReadOnly>true</ReadOnly>
    </MappedFolder>
  </MappedFolders>
  <LogonCommand>
    <Command>explorer C:\Users\WDAGUtilityAccount\Desktop\Financial_Checker_v2.0</Command>
  </LogonCommand>
</Configuration>
```

**3. Executar:**
```batch
# Duplo clique em: FinancialChecker_Sandbox.wsb

# Dentro do Sandbox:
cd Desktop\Financial_Checker_v2.0
INSTALAR_COMPLETO.bat
```

**Vantagens:**
- ✅ Ambiente limpo isolado
- ✅ Não precisa de VM completa
- ✅ Descarta tudo ao fechar
- ✅ Mais rápido que VM

---

## ✅ 3. Validação dos Dois Modos {#validação-modos}

### Checklist de Validação

#### Modo SQLite (Single User)

**Instalação:**
```
□ Sistema instala sem MySQL?
□ Arquivo concilie.db é criado em data/?
□ Tamanho do banco ~300KB inicialmente?
```

**Inicialização:**
```
□ Mensagem "Usando SQLite" aparece?
□ Servidor inicia na porta 8500?
□ Sem erros de conexão?
```

**Funcionalidades:**
```
□ Login funciona (admin/1234)?
□ Menu principal carrega?
□ Pode importar dados?
□ Pode gerar relatórios?
□ Gráficos funcionam?
□ Pode criar novos usuários?
```

**Performance:**
```
□ Interface responde rápido?
□ Importação de Excel funciona?
□ Consultas não travam?
```

#### Modo MySQL (Multi User)

**Instalação:**
```
□ Detecta se MySQL não está rodando?
□ Conecta ao MySQL corretamente?
□ Cria database 'concilie' se não existir?
```

**Inicialização:**
```
□ Mensagem "Usando MySQL" aparece?
□ Servidor inicia na porta 8500?
□ Conexão com banco OK?
```

**Funcionalidades:**
```
□ Login funciona (admin/1234)?
□ Menu principal carrega?
□ Pode importar dados?
□ Pode gerar relatórios?
□ Gráficos funcionam?
□ Múltiplos usuários simultâneos?
```

**Multi-usuário:**
```
□ Dois navegadores conseguem acessar?
□ Mudanças de um aparecem no outro?
□ Sem conflitos de sessão?
```

---

### Scripts de Teste Automatizado

**Criar: `test_installation.bat`**
```batch
@echo off
echo ========================================
echo TESTE AUTOMATIZADO DE INSTALACAO
echo ========================================
echo.

echo [1/5] Verificando Python...
python --version
if errorlevel 1 (
    echo FALHOU: Python nao encontrado
    exit /b 1
)
echo OK
echo.

echo [2/5] Verificando Poetry...
poetry --version
if errorlevel 1 (
    echo FALHOU: Poetry nao encontrado
    exit /b 1
)
echo OK
echo.

echo [3/5] Verificando ambiente Poetry...
poetry env info
if errorlevel 1 (
    echo FALHOU: Ambiente Poetry invalido
    exit /b 1
)
echo OK
echo.

echo [4/5] Testando imports criticos...
poetry run python -c "import pandas; import panel; import sqlalchemy; print('Imports: OK')"
if errorlevel 1 (
    echo FALHOU: Imports com erro
    exit /b 1
)
echo.

echo [5/5] Verificando banco de dados...
poetry run python configure_db.py status
if errorlevel 1 (
    echo FALHOU: Configuracao de banco invalida
    exit /b 1
)
echo OK
echo.

echo ========================================
echo TODOS OS TESTES PASSARAM!
echo ========================================
echo.
echo O sistema esta pronto para uso.
echo Execute "Iniciar Sistema.bat" para iniciar.
echo.
pause
```

---

## 🐛 4. Troubleshooting {#troubleshooting}

### Problemas Comuns na VM/Máquina Limpa

#### ❌ "Python não encontrado"

**Solução:**
```batch
# Baixar Python 3.11:
https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe

# Instalar com:
- ✅ Add Python to PATH
- ✅ Install for all users
```

#### ❌ "Poetry não funciona após instalação"

**Solução:**
```batch
# Adicionar ao PATH manualmente:
# 1. Abrir Variáveis de Ambiente
# 2. Adicionar: %APPDATA%\Python\Scripts

# Ou instalar via pip:
python -m pip install poetry
```

#### ❌ "poetry install muito lento"

**Solução:**
```bash
# Desabilitar keyring (Windows)
poetry config keyring.enabled false

# Usar cache local
poetry config cache-dir C:\poetry-cache

# Reinstalar
poetry install --only main
```

#### ❌ "Erro ao conectar MySQL"

**Soluções:**
```batch
# 1. Verificar se MySQL está rodando
services.msc

# 2. Testar conexão
mysql -u root -p1234

# 3. Criar usuário/banco manualmente
CREATE DATABASE concilie;
CREATE USER 'concilie_user'@'localhost' IDENTIFIED BY '1234';
GRANT ALL ON concilie.* TO 'concilie_user'@'localhost';

# 4. Usar SQLite como alternativa
Iniciar SQLite.bat
```

#### ❌ "Porta 8500 em uso"

**Solução:**
```batch
# Ver quem está usando
netstat -ano | findstr :8500

# Matar processo
taskkill /PID <pid> /F

# Ou mudar porta no código (main.py)
port=8501
```

#### ❌ "Imports demorando muito"

**Solução:**
```batch
# Normal na primeira execução
# Aguarde ~2-3 minutos

# Se travar, Ctrl+C e tentar novamente
```

---

## 📦 Criando Pacote de Distribuição Completo

### Opção 1: Distribuição com Instalador

**Estrutura:**
```
Financial_Checker_v2.0_Distribuicao/
├── INSTALAR_COMPLETO.bat       # Instalador automático
├── Iniciar Sistema.bat          # Iniciar após instalação
├── Configurar Banco.bat         # Configuração de banco
├── LEIA-ME.txt                  # Instruções
├── conf/                        # Configurações
├── modules/                     # Módulos do sistema
├── proc/                        # Processadores
├── data/                        # Dados (incluir concilie.db vazio)
├── pyproject.toml              # Configuração Poetry
├── poetry.lock                 # Versões fixas
└── README_NEW.md               # Documentação
```

### Opção 2: Distribuição com Python Portável

**Usar Python Embedded:**
```
1. Baixar Python Embedded:
   https://www.python.org/ftp/python/3.11.9/python-3.11.9-embed-amd64.zip

2. Extrair na pasta do projeto

3. Instalar dependências no Python embedded

4. Criar launcher.bat que use o Python embedded
```

---

## ✅ Resumo: Como Testar Tudo

### Na Sua Máquina (Desenvolvimento)

```batch
# 1. Testar SQLite
Iniciar SQLite.bat
# Acessar http://localhost:8500
# Testar funcionalidades
# Fechar (Ctrl+C)

# 2. Testar MySQL
Iniciar MySQL.bat
# Acessar http://localhost:8500
# Testar funcionalidades
# Fechar (Ctrl+C)

# 3. Verificar alternância
Configurar Banco.bat
# Opção [3] Ver Status
```

### Em Máquina Limpa (VM/Sandbox)

```batch
# 1. Copiar projeto para VM

# 2. Executar instalação completa
INSTALAR_COMPLETO.bat

# 3. Testar
Iniciar Sistema.bat

# 4. Validar checklist completo
```

---

**Próximo Passo:** Criar INSTALAR_COMPLETO.bat e testar em VM!
