# Concilie API — Backend FastAPI

Backend Python/FastAPI do sistema Concilie de reconciliação financeira.

## Pré-requisitos

- Python 3.11+
- [Poetry](https://python-poetry.org/) 1.8+

## Setup

```bash
# Na raiz do monorepo
cd apps/api

# Instalar dependências
poetry install

# Copiar e preencher variáveis de ambiente
cp .env.example .env
# Edite .env com as configurações locais
```

## Variáveis de Ambiente

Veja `.env.example` para a lista completa. Configurações principais:

| Variável | Descrição | Padrão |
|----------|-----------|--------|
| `DATABASE_TYPE` | `sqlite` ou `mysql` | `sqlite` |
| `SQLITE_DB_PATH` | Path para o arquivo .db | `../../data/concilie.db` |
| `SECRET_KEY` | Chave JWT (mínimo 32 chars) | — (obrigatório) |
| `CORS_ORIGINS` | JSON array de origens permitidas | `["http://localhost:3000"]` |

## Executar

```bash
# Modo desenvolvimento (hot reload)
poetry run uvicorn app.main:app --reload --port 8000

# Swagger UI disponível em: http://localhost:8000/docs
```

## Testes

```bash
# Todos os testes
poetry run pytest tests/ -v

# Com relatório de cobertura
poetry run pytest tests/ -v --cov=app --cov-report=term-missing
```

## Lint

```bash
# Verificar
poetry run ruff check app/

# Auto-corrigir
poetry run ruff check app/ --fix
```

## Estrutura

```
app/
├── api/v1/endpoints/   # Rotas FastAPI
├── core/               # Config, database, security
├── models/             # Modelos SQLAlchemy
├── repositories/       # Camada de acesso a dados
├── schemas/            # Pydantic schemas
├── services/           # Lógica de negócio
└── main.py             # Entry point
tests/                  # Suite de testes pytest
```
