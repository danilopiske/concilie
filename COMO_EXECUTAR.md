# 🚀 Como Executar o Financial Checker (Next.js + FastAPI)

Este guia explica como executar o projeto completo com Frontend Next.js e Backend FastAPI.

---

## 📋 Pré-requisitos

### Instalações Necessárias

1. **Node.js** (v18 ou superior)
   - Download: https://nodejs.org/
   - Verificar: `node --version`

2. **pnpm** (v8 ou superior)
   ```powershell
   npm install -g pnpm
   # Verificar: pnpm --version
   ```

3. **Python** (3.10, 3.11 ou 3.12)
   - Download: https://www.python.org/
   - Verificar: `python --version`

4. **Poetry** (gerenciador de pacotes Python)
   ```powershell
   pip install poetry
   # Verificar: poetry --version
   ```

5. **MySQL** (opcional, pode usar SQLite)
   - Download: https://dev.mysql.com/downloads/installer/
   - Ou use SQLite (já vem com Python)

---

## 🗂️ Estrutura do Projeto

```
Financial_P/
├── apps/
│   ├── api/          # Backend FastAPI (Python/Poetry)
│   │   ├── app/
│   │   ├── pyproject.toml
│   │   └── .env
│   └── web/          # Frontend Next.js (TypeScript/pnpm)
│       ├── src/
│       ├── package.json
│       └── .env.local
├── conf/             # Sistema legado Panel (Python)
├── modules/          # Sistema legado Panel (Python)
├── proc/             # Sistema legado Panel (Python)
├── main.py           # Sistema legado Panel
├── package.json      # Configuração monorepo
└── pyproject.toml    # Sistema legado Poetry
```

---

## ⚙️ Configuração Inicial

### 1️⃣ Configurar o Banco de Dados

**OPÇÃO MAIS FÁCIL: Execute o script automatizado**

```powershell
# Execute no diretório raiz do projeto:
"Configurar Stack Moderno.bat"
```

Escolha:
- **[1] SQLite** - Single User (recomendado para desenvolvimento)
- **[2] MySQL** - Multi User (recomendado para produção)

O script configura automaticamente o `.env` com as configurações corretas.

---

**OPÇÃO MANUAL:**

#### Passo 1: Navegar para a pasta da API
```powershell
cd "d:\Financial Checker base\Financial_P\apps\api"
```

#### Passo 2: Instalar dependências com Poetry
```powershell
poetry install
```

#### Passo 3: Escolher template de configuração

**Para SQLite (Single User):**
```powershell
copy .env.sqlite .env
```

**Para MySQL (Multi User):**
```powershell
copy .env.mysql .env
notepad .env  # Edite MYSQL_PASSWORD
```

#### Passo 4: Verificar configuração

**Arquivo `.env.sqlite` (já pré-configurado):**
```env
DATABASE_TYPE=sqlite
SQLITE_DB_PATH=../../data/concilie.db
DEBUG_SQL=false
SECRET_KEY=your-secret-key-change-in-production
```

**Arquivo `.env.mysql` (configure a senha):**
```env
DATABASE_TYPE=mysql
MYSQL_SERVER=localhost
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=      # ← DEFINA SUA SENHA AQUI
MYSQL_DB=bd_conciliacao
```

#### Passo 4: Configurar o banco de dados

**Opção A - Usar SQLite (mais simples):**
```powershell
# Voltar para a raiz do projeto
cd ../..

# Configurar SQLite
python configure_db.py sqlite
```

**Opção B - Usar MySQL:**
```powershell
# Voltar para a raiz do projeto
cd ../..

# Configurar MySQL
python configure_db.py mysql

# Ou usar o configurador visual:
.\Configurar Banco.bat
```

---

### 2️⃣ Configurar o Frontend (Next.js)

#### Passo 1: Navegar para a pasta web
```powershell
cd "d:\Financial Checker base\Financial_P\apps\web"
```

#### Passo 2: Instalar dependências com pnpm
```powershell
pnpm install
```

#### Passo 3: Configurar variáveis de ambiente

Crie o arquivo `.env.local`:
```powershell
notepad .env.local
```

**Conteúdo do `.env.local`:**
```env
# URL da API Backend
NEXT_PUBLIC_API_URL=http://localhost:8000

# Outras configurações
NEXT_PUBLIC_APP_NAME=Financial Checker
```

---

## 🚀 Executar o Projeto

### ⚡ MODO RÁPIDO - Scripts Automatizados

**Execute os scripts .bat do diretório raiz:**

#### Para SQLite (Single User):
```powershell
"Iniciar Stack Moderno - SQLite.bat"
```

#### Para MySQL (Multi User):
```powershell
"Iniciar Stack Moderno - MySQL.bat"
```

Esses scripts:
- ✅ Verificam dependências (Poetry, pnpm)
- ✅ Verificam configuração do .env
- ✅ Abrem 2 terminais automaticamente (Backend + Frontend)
- ✅ Iniciam os serviços com logs separados

**URLs após iniciar:**
- Backend: http://localhost:8000
- Frontend: http://localhost:3000
- API Docs: http://localhost:8000/docs

---

### 🔧 MODO MANUAL - Passo a Passo

#### Opção 1: Executar TUDO de uma vez (Recomendado)

**Da raiz do projeto:**
```powershell
cd "d:\Financial Checker base\Financial_P"

# Iniciar Backend E Frontend simultaneamente
pnpm dev
```

Isso executará:
- ✅ Backend FastAPI em `http://localhost:8000`
- ✅ Frontend Next.js em `http://localhost:3000`

---

#### Opção 2: Executar Backend e Frontend separadamente

#### Terminal 1 - Backend (FastAPI)
```powershell
cd "d:\Financial Checker base\Financial_P\apps\api"

# Ativar ambiente Poetry e executar
poetry run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Backend estará disponível em:**
- API: http://localhost:8000
- Documentação Swagger: http://localhost:8000/docs
- Documentação ReDoc: http://localhost:8000/redoc

#### Terminal 2 - Frontend (Next.js)
```powershell
cd "d:\Financial Checker base\Financial_P\apps\web"

# Executar Next.js
pnpm dev
```

**Frontend estará disponível em:**
- Aplicação: http://localhost:3000

---

### Opção 3: Executar apenas o Frontend Next.js
```powershell
cd "d:\Financial Checker base\Financial_P"
pnpm dev:web
```

---

## 🔄 Alternar Entre SQLite e MySQL

Você pode alternar entre bancos de dados facilmente:

### Método 1: Script Automatizado (RECOMENDADO)
```powershell
# Execute no diretório raiz:
"Configurar Stack Moderno.bat"
```
Escolha a opção desejada ([1] SQLite ou [2] MySQL)

### Método 2: Manual
```powershell
cd apps/api

# Para SQLite:
copy .env.sqlite .env

# Para MySQL:
copy .env.mysql .env
notepad .env  # Configure MYSQL_PASSWORD
```

**IMPORTANTE:**
- Após alternar, **reinicie o backend** para aplicar as mudanças
- SQLite cria o banco automaticamente em `data/concilie.db`
- MySQL requer serviço MySQL rodando e banco `bd_conciliacao` criado

---

## 🧪 Verificar se está funcionando

### 1. Testar o Backend
Abra o navegador em: http://localhost:8000/docs

Você verá a documentação interativa da API (Swagger UI).

### 2. Testar o Frontend
Abra o navegador em: http://localhost:3000

Você verá a interface do Financial Checker.

### 3. Testar a comunicação
No Frontend, faça login ou execute qualquer ação que chame a API.
Verifique no terminal do Backend se há logs de requisições.

---

## 🛠️ Comandos Úteis

### Backend (FastAPI)
```powershell
cd "d:\Financial Checker base\Financial_P\apps\api"

# Instalar dependências
poetry install

# Adicionar nova dependência
poetry add nome-pacote

# Executar servidor
poetry run uvicorn app.main:app --reload

# Executar testes
poetry run pytest

# Formatar código
poetry run black app/
poetry run isort app/

# Ver dependências instaladas
poetry show
```

### Frontend (Next.js)
```powershell
cd "d:\Financial Checker base\Financial_P\apps\web"

# Instalar dependências
pnpm install

# Adicionar nova dependência
pnpm add nome-pacote

# Executar desenvolvimento
pnpm dev

# Build para produção
pnpm build

# Executar produção
pnpm start

# Linter
pnpm lint
```

### Monorepo (Raiz)
```powershell
cd "d:\Financial Checker base\Financial_P"

# Executar tudo em paralelo
pnpm dev

# Build de tudo
pnpm build

# Executar apenas o web
pnpm dev:web
```

---

## 🐛 Solução de Problemas

### Erro: "pnpm: comando não encontrado"
```powershell
npm install -g pnpm
```

### Erro: "poetry: comando não encontrado"
```powershell
pip install poetry
# Ou
python -m pip install poetry
```

### Erro: "Porta 8000 já em uso"
Mate o processo que está usando a porta:
```powershell
# Encontrar processo
netstat -ano | findstr :8000

# Matar processo (substitua PID pelo número encontrado)
taskkill /PID <PID> /F
```

### Erro: "Porta 3000 já em uso"
```powershell
# Encontrar processo
netstat -ano | findstr :3000

# Matar processo
taskkill /PID <PID> /F

# Ou use outra porta
pnpm dev -- -p 3001
```

### Erro de conexão com banco de dados

**SQLite:**
```powershell
# Verificar se o arquivo existe
dir data\concilie.db

# Se não existir, criar:
python configure_db.py sqlite
```

**MySQL:**
```powershell
# Verificar se MySQL está rodando
mysql -u root -p

# Criar banco de dados
CREATE DATABASE financial_checker;

# Atualizar .env com credenciais corretas
```

### Erro: "Module not found" no Backend
```powershell
cd apps/api
poetry install
```

### Erro: "Package not found" no Frontend
```powershell
cd apps/web
pnpm install
```

---

## 📦 Build para Produção

### Backend (FastAPI)
```powershell
cd apps/api

# Instalar apenas dependências de produção
poetry install --no-dev

# Executar com Uvicorn otimizado
poetry run uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### Frontend (Next.js)
```powershell
cd apps/web

# Build otimizado
pnpm build

# Executar build
pnpm start
```

---

## 🔄 Sistema Legado (Panel)

Se precisar executar o sistema legado em Panel:

```powershell
cd "d:\Financial Checker base\Financial_P"

# Instalar dependências
poetry install

# Configurar banco
python configure_db.py

# Executar sistema Panel
python main.py
# Ou
.\Iniciar Sistema.bat
```

**Sistema Panel estará em:** http://localhost:8500

---

## 📚 Documentação Adicional

- **API Documentation:** http://localhost:8000/docs
- **Next.js Documentation:** https://nextjs.org/docs
- **FastAPI Documentation:** https://fastapi.tiangolo.com/
- **Poetry Documentation:** https://python-poetry.org/docs/
- **pnpm Documentation:** https://pnpm.io/

---

## 🎯 Próximos Passos

1. ✅ Configurar banco de dados
2. ✅ Executar Backend FastAPI
3. ✅ Executar Frontend Next.js
4. ✅ Fazer login no sistema
5. ✅ Testar funcionalidades

---

## 📞 Suporte

Se encontrar problemas, verifique:
1. Todos os pré-requisitos estão instalados
2. Variáveis de ambiente configuradas corretamente
3. Banco de dados está rodando (se MySQL)
4. Portas 3000 e 8000 estão livres

---

**Desenvolvido com ❤️ pela equipe Financial Checker**
