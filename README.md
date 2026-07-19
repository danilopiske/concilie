# Concilie (Financial )

> **A Hybrid Financial Reconciliation Platform** combining a robust Python core with a modern Next.js interface.

![Status](https://img.shields.io/badge/Status-Hybrid%20Migration-yellow)
![Backend](https://img.shields.io/badge/Backend-FastAPI%20%2B%20Python-blue)
![Frontend](https://img.shields.io/badge/Frontend-Next.js%20(React)-black)
![Database](https://img.shields.io/badge/Database-MySQL%20%7C%20SQLite-green)

## 📋 Overview

Concilie is a system designed to process, validate, and reconcile large volumes of financial data (Cards, PIX, etc.). It features a unique **Dual-Mode Architecture** that allows it to run as a robust server application (MySQL) or a portable standalone executable (SQLite).

### Key Features
- **Smart Import**: Heuristic detection of headers in messy Excel/CSV files.
- **Dual-Database Core**: Seamlessly switch between MySQL (Production) and SQLite (Distribution) without code changes.
- **Hybrid UI**: 
    - **Modern**: Next.js + Tailwind web interface.
    - **Legacy**: Panel-based interface for rapid data tools.

---

## 🏗️ Architecture

The system is split into three main layers:

1.  **Core (`proc/`, `conf/`)**: The business logic engine. Handles invalid file parsing, normalization rules ("De-Para"), and database abstraction.
2.  **API (`apps/api`)**: A FastAPI service that exposes the Core logic to the web.
3.  **Web (`apps/web`)**: A Next.js frontend application.

👉 **View the full [Architecture Diagram](docs/ARCHITECTURE.md)**

---

## 🚀 Getting Started

### Prerequisites
- Python 3.11+
- Node.js 18+ & pnpm
- (Optional) MySQL Server 8.0+

### 1. Installation

**Backend Setup**
```bash
cd apps/api
poetry install
```

**Frontend Setup**
```bash
cd apps/web
pnpm install
```

### 2. Database Configuration (Critical)

The system needs to know which database mode to use.

**Option A: Developer Mode (MySQL)**
*Requires a running MySQL server on localhost:3306*
```bash
python configure_db.py mysql
```

**Option B: Distribution Mode (SQLite)**
*Runs immediately with a local file in `data/concilie.db`*
```bash
python configure_db.py sqlite
```

### 3. Running the System

You can run the full stack using the provided scripts in the root directory:

- **MySQL Mode**: Run `Iniciar Stack Moderno - MySQL.bat`
- **SQLite Mode**: Run `Iniciar Stack Moderno - SQLite.bat`

Or manually:

```bash
# Terminal 1 (Backend)
cd apps/api
poetry run uvicorn app.main:app --reload --port 8000

# Terminal 2 (Frontend)
cd apps/web
pnpm dev
```

---

## 🧪 Testing

```bash
# Backend — pytest
cd apps/api
poetry run pytest tests/ -v

# Frontend — E2E Playwright (requer stack rodando)
cd apps/web
pnpm test:e2e
```

## 🔐 Secrets

Segredos (chaves de API, senhas, `SECRET_KEY` JWT, etc.) **nunca** são commitados em texto puro. Eles ficam consolidados e criptografados em `secrets.enc.env` (via [SOPS](https://github.com/getsops/sops) + [age](https://github.com/FiloSottile/age)), que é o único artefato de segredos versionado no repositório.

**Para descriptografar e gerar seu `.env` local:**
```bash
sops -d secrets.enc.env > .env
```

**Regras:**
- A chave privada `age` usada para descriptografar **fica fora do repositório** (cofre de segredos do time / gerenciador de secrets da VPS) — nunca é commitada nem compartilhada em chat/log.
- **Nunca** commitar `.env`, `.env.local` ou qualquer variante com valores reais — o `.gitignore` já bloqueia esses padrões (`.env*`), com exceção explícita para `secrets.enc.env` e `*.enc.env`.
- Para saber quais variáveis existem (sem valores), veja `.env.example`, `apps/api/.env.example` e `apps/web/.env.example`.
- Ao adicionar uma nova variável de segredo: edite o `.env` local, adicione o nome (vazio) no `.env.example` correspondente, e recriptografe com `sops -e --input-type dotenv --output-type dotenv --filename-override secrets.enc.env .env > secrets.enc.env`.

---

## ✅ CI/CD

O projeto usa GitHub Actions com dois workflows:

- **`ci.yml`** — Executa em todo PR e push para `main`: lint (ruff + eslint), typecheck, pytest, build Next.js
- **`e2e.yml`** — Executa após CI passar: smoke tests E2E com Playwright

---

## 📚 Documentation

- **[Evaluation Report](docs/EVALUATION_REPORT.md)**: Current state assessment and code quality analysis.
- **[Architecture](docs/ARCHITECTURE.md)**: System design and data flow.
- **[System Description](docs/DESCRITIVO_SISTEMA.md)**: Functional details of modules.

---

## 🛠️ Project Structure

```
Financial_P/
├── apps/
│   ├── api/          # FastAPI Backend (The Bridge)
│   └── web/          # Next.js Frontend (The Face)
├── proc/             # Core Business Logic (Legacy)
├── conf/             # Configuration & DB Adapters
├── data/             # SQLite storage (concilie.db)
├── docs/             # Documentation
└── main.py           # Legacy Panel Entry Point
```

---

**Version 1.8 - Hybrid Migration Stage**
User: Danilo Piske
