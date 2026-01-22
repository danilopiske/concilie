# 🎯 Scripts de Inicialização - Financial Checker v2.0

## 📋 Visão Geral dos Scripts

Este diretório contém scripts para facilitar a execução do sistema em **modo legado (Panel)** e **modo moderno (Next.js + FastAPI)**.

---

## 🆕 Stack Moderno (Next.js + FastAPI)

### 1️⃣ Configurar Banco de Dados
```powershell
"Configurar Stack Moderno.bat"
```
**O que faz:**
- Menu interativo para escolher SQLite ou MySQL
- Copia template correto (`.env.sqlite` ou `.env.mysql`) para `apps/api/.env`
- Solicita configuração de senha MySQL (se aplicável)

**Quando usar:**
- Primeira execução do sistema
- Alternar entre SQLite e MySQL
- Recriar configuração do .env

---

### 2️⃣ Iniciar Sistema - SQLite
```powershell
"Iniciar Stack Moderno - SQLite.bat"
```
**O que faz:**
- Verifica dependências (Poetry, pnpm)
- Confirma configuração SQLite no .env
- Abre 2 terminais automaticamente:
  - Terminal 1: Backend FastAPI (porta 8000)
  - Terminal 2: Frontend Next.js (porta 3000)

**Requisitos:**
- `.env` configurado para SQLite
- Dependências instaladas (`poetry install`, `pnpm install`)

**URLs:**
- Frontend: http://localhost:3000
- Backend: http://localhost:8000
- API Docs: http://localhost:8000/docs

---

### 3️⃣ Iniciar Sistema - MySQL
```powershell
"Iniciar Stack Moderno - MySQL.bat"
```
**O que faz:**
- Verifica se MySQL está rodando
- Verifica dependências (Poetry, pnpm)
- Confirma configuração MySQL no .env
- Abre 2 terminais automaticamente:
  - Terminal 1: Backend FastAPI (porta 8000)
  - Terminal 2: Frontend Next.js (porta 3000)

**Requisitos:**
- Serviço MySQL rodando (`net start MySQL80`)
- `.env` configurado para MySQL com senha correta
- Banco `bd_conciliacao` criado
- Dependências instaladas

**URLs:**
- Frontend: http://localhost:3000
- Backend: http://localhost:8000
- API Docs: http://localhost:8000/docs

---

## 🔧 Sistema Legado (Panel/HoloViz)

### Configurar Banco
```powershell
"Configurar Banco.bat"
```
**O que faz:**
- Executa `configure_db.py` para setup de banco
- Configuração para sistema Panel legado

---

### Iniciar MySQL (Legado)
```powershell
"Iniciar MySQL.bat"
```
**O que faz:**
- Inicia sistema Panel com MySQL
- Usa `main.py` (interface Panel/HoloViz)

---

### Iniciar SQLite (Legado)
```powershell
"Iniciar SQLite.bat"
```
**O que faz:**
- Inicia sistema Panel com SQLite
- Usa `main.py` (interface Panel/HoloViz)

---

## 🆚 Comparação: Legado vs Moderno

| Aspecto | Sistema Legado | Stack Moderno |
|---------|---------------|---------------|
| **Frontend** | Panel/HoloViz (Python) | Next.js (TypeScript) |
| **Backend** | Integrado ao main.py | FastAPI separado |
| **Performance** | Carregamento lento | SPA rápido |
| **Manutenção** | Difícil (monolito) | Fácil (modular) |
| **API** | Não exposta | RESTful documentada |
| **Scripts** | `Iniciar MySQL.bat` | `Iniciar Stack Moderno - MySQL.bat` |

---

## 🚀 Fluxo de Uso Recomendado

### Primeira Vez (Setup)
1. **Configurar banco:**
   ```powershell
   "Configurar Stack Moderno.bat"
   ```
   Escolha [1] SQLite (mais fácil) ou [2] MySQL

2. **Instalar dependências:**
   ```powershell
   # Backend
   cd apps/api
   poetry install

   # Frontend
   cd apps/web
   pnpm install
   ```

3. **Iniciar sistema:**
   ```powershell
   # Se escolheu SQLite:
   "Iniciar Stack Moderno - SQLite.bat"

   # Se escolheu MySQL:
   "Iniciar Stack Moderno - MySQL.bat"
   ```

---

### Uso Diário
```powershell
# Apenas execute o script apropriado:
"Iniciar Stack Moderno - SQLite.bat"
# OU
"Iniciar Stack Moderno - MySQL.bat"
```

---

### Alternar Banco de Dados
1. **Feche o sistema** (Ctrl+C nos terminais)
2. **Reconfigure:**
   ```powershell
   "Configurar Stack Moderno.bat"
   ```
3. **Reinicie com novo banco:**
   ```powershell
   "Iniciar Stack Moderno - [SQLite/MySQL].bat"
   ```

---

## 🛠️ Troubleshooting

### ❌ "MySQL is not running"
**Solução:**
```powershell
net start MySQL80
```

### ❌ "Poetry not found"
**Solução:**
```powershell
pip install poetry
```

### ❌ "pnpm not found"
**Solução:**
```powershell
npm install -g pnpm
```

### ❌ "Port 8000 already in use"
**Solução:**
```powershell
# Encontrar processo usando porta:
netstat -ano | findstr :8000

# Matar processo (substitua <PID>):
taskkill /PID <PID> /F
```

### ❌ ".env not found"
**Solução:**
```powershell
"Configurar Stack Moderno.bat"
```

### ❌ "Access denied for user 'root'"
**Solução:**
```powershell
# Edite o .env e corrija a senha:
notepad apps\api\.env

# Procure: MYSQL_PASSWORD=
# Configure: MYSQL_PASSWORD=sua_senha_real
```

---

## 📚 Documentação Adicional

- **[COMO_EXECUTAR.md](COMO_EXECUTAR.md)** - Guia completo de execução
- **[.github/agents/agentconcilie.md](.github/agents/agentconcilie.md)** - Guia técnico para IA/desenvolvedores
- **API Docs:** http://localhost:8000/docs (quando backend rodando)

---

## 🎯 Recomendações

### Para Desenvolvimento:
✅ Use **SQLite** (sem necessidade de MySQL rodando)
✅ Script: `Iniciar Stack Moderno - SQLite.bat`

### Para Produção/Multi-User:
✅ Use **MySQL** (múltiplos usuários simultâneos)
✅ Script: `Iniciar Stack Moderno - MySQL.bat`

---

**Migração em andamento:** Sistema legado (Panel) está sendo gradualmente substituído pelo stack moderno (Next.js + FastAPI). Novos módulos devem ser desenvolvidos apenas no stack moderno.
