# Inventário de Dívida Técnica — Concilie

> Criado em: 2026-03-20 | Referência: Stories 2.1, 2.2, 2.3, 2.4

## Legenda

| Campo | Valores |
|-------|---------|
| Impacto | **H** (Alto) · **M** (Médio) · **L** (Baixo) |
| Esforço | **P** (Pequeno ≤ 1 dia) · **M** (Médio 2-3 dias) · **G** (Grande 1 semana+) |
| Status | `open` · `in-progress` · `resolved` |

---

## Backend (apps/api)

| # | Item | Impacto | Esforço | Owner | Status | Referência |
|---|------|---------|---------|-------|--------|------------|
| B-01 | `relatorio_service.py` — SessionFactory injetada via `SessionLocal()`, closure `update_progress` extraída para `_update_progress(session, task, pct, msg)` | H | G | @dev | resolved | Story 2.1, Story 3.4 |
| B-02 | `reconciliation_core.py` — acoplamento direto com módulo legado `proc/`, importa `sys.path.append` hardcoded | H | G | @dev | open | Story 2.1 |
| B-03 | `app/models/depara.py` — arquivo sem referências em endpoints/repositories confirmado via grep; arquivo removido. Modelo real é `legacy_depara.py` | M | P | @dev | resolved | Story 2.4, Story 3.4 |
| B-04 | CORS `allow_origins` — em desenvolvimento usa `["*"]` potencialmente. Confirmar configuração para produção via variável de ambiente | H | P | @dev | resolved | Story 2.1, Story 3.2 |
| B-05 | Ausência de testes unitários para camada de serviços (`services/`) — apenas integração via pytest | M | G | @dev | open | Story 2.3 |
| B-06 | `depara.py` endpoint `/ler-cabecalhos` usa `sys.path.append` com path hardcoded como fallback (`d:/Financial  base/...`) | M | P | @dev | resolved | Story 2.1, Story 3.3 |
| B-07 | `alembic` instalado mas sem migrations criadas — schema gerenciado manualmente | M | M | @dev | open | Story 2.1 |

## Frontend (apps/web)

| # | Item | Impacto | Esforço | Owner | Status | Referência |
|---|------|---------|---------|-------|--------|------------|
| F-01 | TipTap `useEditor` com extension recriada dentro de `useEffect` a cada render — causa re-criação desnecessária da extensão Highlight | M | P | @dev | open | Story 2.2, Story 2.3 |
| F-02 | `RelatorioPage` — filtros de data sem validação de intervalo máximo; usuário pode solicitar range de anos inteiros | M | P | @dev | open | Story 2.2 |
| F-03 | Sem testes unitários para componentes React (apenas E2E Playwright) | M | G | @dev | open | Story 2.3 |
| F-04 | `package.json` sem script `format` (Prettier) — formatação manual ou via editor apenas | L | P | @dev | open | Story 2.4 |

## CI/CD e Infraestrutura

| # | Item | Impacto | Esforço | Owner | Status | Referência |
|---|------|---------|---------|-------|--------|------------|
| C-01 | GitHub Secrets `DATABASE_URL`, `SECRET_KEY` não configurados no repositório remoto — CI usa valores hardcoded para SQLite | H | P | @devops | resolved | Story 2.4, Story 3.2 |
| C-02 | Pipeline E2E (`e2e.yml`) não tem banco de dados persistente entre testes — cada run parte de SQLite vazio sem seed de dados | M | M | @devops | open | Story 2.3 |
| C-03 | Sem pipeline de deploy automatizado (CD) — deploy é manual via bat scripts | M | G | @devops | open | — |

## Legacy (proc/, conf/, modules/)

| # | Item | Impacto | Esforço | Owner | Status | Referência |
|---|------|---------|---------|-------|--------|------------|
| L-01 | Módulos legados em `proc/` e `conf/` ainda são referenciados pelo backend FastAPI — acoplamento bidirecional impede refatoração independente | H | G | @architect | open | Story 2.1 |
| L-02 | `configure_db.py` na raiz — script de configuração manual que manipula arquivos `.env.active`; frágil e não testado | M | M | @dev | open | Story 2.1 |
| L-03 | `main.py` legado (Panel) mantido na raiz — entry point da UI antiga ainda funcional mas sem manutenção ativa | L | M | @dev | open | — |

---

## Itens Críticos (Impacto H) — Follow-up

Os itens de impacto alto abaixo devem ter story de follow-up criada antes do Sprint 3:

| Item | Story Sugerida | Prioridade |
|------|---------------|------------|
| B-01 — `relatorio_service.py` refactor | Story 3.x: Refatorar camada de serviços de reconciliação | Alta |
| B-02 — Desacoplar `reconciliation_core.py` do legado | Story 3.x: Criar abstração entre FastAPI e módulos proc/ | Alta |
| B-04 — CORS produção | Story 3.x: Configuração de ambientes (dev/staging/prod) | Média |
| C-01 — GitHub Secrets | Configurar via `@devops` no repositório remoto | Imediata |
| L-01 — Acoplamento legado | Story 3.x: Migration plan dos módulos proc/ para app/ | Alta |

---

## Histórico de Resoluções

| Data | Item | Descrição | Story |
|------|------|-----------|-------|
| 2026-03-20 | B-04 — CORS produção | `ALLOWED_ORIGINS_STR` env var adicionada ao config.py | 3.2 |
| 2026-03-20 | C-01 — GitHub Secrets | `ci.yml` migrado para `${{ secrets.SECRET_KEY_CI }}`, guia criado | 3.2 |
| 2026-03-20 | `.env.mysql` exposto | Removido do git tracking via `git rm --cached` | 2.4 |
| 2026-03-20 | ruff 538 erros | Reduzido para 0 com `--fix`, `--unsafe-fixes` e config de ignores | 2.4 |
| 2026-03-20 | `depara.py` corrompido | Reconstruído como modelo SQLAlchemy válido | 2.4 |
| 2026-03-20 | `e2e.yml` services malformado | Removido bloco services inválido | 2.4 |
| 2026-03-20 | `e2e.yml` cross-workflow deps | Migrado de `needs: [lint-web]` para `workflow_run` trigger | 2.4 |
