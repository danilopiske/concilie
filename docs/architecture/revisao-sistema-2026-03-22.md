# Revisão Completa do Sistema — 2026-03-22

## Resumo Executivo

| Categoria | Achado | Severidade |
|-----------|--------|------------|
| Autenticação | 2 endpoints não-login sem `get_current_user` | MÉDIA |
| Autorização | Apenas 2 de 32 endpoints protegidos usam `require_role()` | ALTA |
| Banco de dados | 3 FKs sem índice | MÉDIA |
| Logging | 11 `print()` que deveriam ser `logger` | BAIXA |
| Validação | ~20+ campos string sem constraints | MÉDIA |
| Testes | 14 endpoints sem cobertura (~42% gap) | ALTA |

---

## 1. Endpoints sem autenticação

- `login.py` — INTENCIONAL (público)
- `recuperacao.py` — REVISAR (recuperação de senha — intencional?)
- `termos.py` — REVISAR (termos — intencional?)
- `depara.py` — REVISAR (mapeamento — deve ser protegido?)

**Ação:** Confirmar se `recuperacao`, `termos` e `depara` devem ser públicos. Documentar decisão.

---

## 2. Endpoints sem require_role (ALTA prioridade)

Apenas `usuarios.py` usa `require_role(["admin"])` (2 endpoints). Os demais 32 endpoints com `get_current_user` não verificam perfil.

**Endpoints que devem ter restrição de role:**

| Endpoint | Role sugerido |
|----------|---------------|
| `auditoria.py` | admin |
| `sistema.py` | admin |
| `usuarios.py` (todos) | admin |
| `configuracoes` | admin |
| `gestao.py` (escrita) | admin, operador |
| `importacao_async.py` | admin, operador |
| `calculos` (escrita) | admin, operador |
| `dashboard.py` | admin, operador, visualizador |
| `relatorios.py` (leitura) | admin, operador, visualizador |

**Ação:** Story 3.41 — aplicar `require_role()` nos endpoints críticos (fase 2 da 3.39).

---

## 3. FKs sem índice

| Tabela | Coluna | Impacto |
|--------|--------|---------|
| `import_task` | `cliente_id` | lento em importações massivas |
| `usuario_clientes` | `cliente_id` | lento em lookup de escopo |
| `usuario_contextos` | `contexto_id` | lento em filtragem |

**Ação:** Migração 0003 com os 3 índices faltantes.

---

## 4. print() em vez de logger

| Arquivo | Linhas | Count |
|---------|--------|-------|
| `abusividade_service.py` | 124 | 1 |
| `ai_service.py` | 45, 58, 136 | 3 |
| `import_service.py` | 136, 144, 290, 349, 418, 549 | 6 |
| `relatorio_service.py` | 97, 203 | 2 |

**Ação:** Substituir 12 ocorrências por `logger.warning/error`.

---

## 5. Schemas sem validação

Campos sem `min_length`, `max_length` ou `pattern`:
- `cliente.py` — `nome_fantasia`, `razao_social`, `cnpj`
- `extrato_cliente.py` — `nome_arquivo`, `tipo`
- `calculo.py` — `calc_id`, `calc_usuario`
- `contestacao.py` — campos HTML

**Risco:** DoS via payload gigante; injeção indireta.
**Ação:** Adicionar `Field(max_length=N)` nos campos expostos na API.

---

## 6. Cobertura de testes — 42% gap

**Sem testes (14 endpoints críticos):**
`abusividade`, `ai`, `alertas_config`, `auditoria`, `clientes`, `contestacoes`,
`dashboard`, `extratos_cliente`, `gestao`, `importacao_async`, `notificacoes`,
`sistema`, `taxas`, `taxas_contratadas`

**Meta:** 80% de cobertura → precisamos de testes para pelo menos os 8 endpoints business-critical.

---

## Roadmap de Ações

| Story | Descrição | Prioridade |
|-------|-----------|------------|
| 3.41 | Aplicar `require_role()` em todos os endpoints (fase 2 da 3.39) | ALTA |
| 3.42 | Migração 0003 — índices FK faltantes + converter print → logger | MÉDIA |
| 3.43 | Testes para endpoints críticos: dashboard, taxas, contestacoes, gestao | ALTA |
| 3.44 | Validação de schemas: Field constraints nos endpoints expostos | MÉDIA |
