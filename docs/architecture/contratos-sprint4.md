# Contratos Técnicos — Sprint 4 (Stories 3.10–3.15)

> **Emitido por:** @architect (Aria)
> **Data:** 2026-03-20
> **Propósito:** Contratos de API, dados e decisões técnicas para orientar implementação das stories 3.10–3.15

---

## 1. Grafo de Dependências

```
3.10 Dashboard KPIs          ─── independente (lê dados existentes)
3.11 Taxas Contratadas        ─── independente (novo model)
         │
         ▼
3.12 Contestação              ─── DEPENDE de 3.11 (DesvioTaxa)
         │
         ▼
3.13 Exportação PDF           ─── DEPENDE de 3.12 (contestacoes/{id}/download)
                               └── DEPENDE de relatorio_task (já existente)
3.14 Assistente IA            ─── independente (ai_service já existe — estender)
3.15 Notificações             ─── DEPENDE de 3.11, 3.12, 3.13 (disparos nos services)
```

---

## 2. Sequência Recomendada de Implementação

| Ordem | Story | Justificativa |
|-------|-------|---------------|
| 1 | **3.10** | Zero dependências, entrega valor imediato, não altera models existentes |
| 2 | **3.11** | Fundação para 3.12; model `TaxaContratada` novo e isolado |
| 3 | **3.12** | Requer 3.11 (`DesvioTaxa`); produz `html_carta` que 3.13 exporta |
| 4 | **3.13** | Requer `html_carta` da 3.12 para PDF de contestação |
| 5 | **3.14** | Independente — pode ser paralela com 3.13 se time permitir |
| 6 | **3.15** | Última — integra-se em todos os services anteriores |

---

## 3. Contratos de API — Todos os Novos Endpoints

| Método | Rota | JWT | Request | Response |
|--------|------|-----|---------|----------|
| GET | `/dashboard/resumo` | ✅ | — | `DashboardResumo` |
| GET | `/dashboard/atividade-recente` | ✅ | — | `List[EventoAtividade]` |
| GET | `/clientes/{id}/taxas-contratadas` | ✅ | `?vigente=bool` | `List[TaxaContratadaOut]` |
| POST | `/clientes/{id}/taxas-contratadas` | ✅ | `TaxaContratadaIn` | `TaxaContratadaOut` |
| PUT | `/clientes/{id}/taxas-contratadas/{taxa_id}` | ✅ | `TaxaContratadaIn` | `TaxaContratadaOut` |
| DELETE | `/clientes/{id}/taxas-contratadas/{taxa_id}` | ✅ | — | `{"ok": true}` |
| GET | `/clientes/{id}/taxas-contratadas/comparacao` | ✅ | `?processamento_id=X` | `List[DesvioTaxa]` |
| GET | `/clientes/{id}/taxas-contratadas/historico-desvios` | ✅ | — | `List[DesvioTaxaHistorico]` |
| POST | `/contestacoes/gerar` | ✅ | `GerarContestacaoIn` | `ContestacaoOut` |
| GET | `/contestacoes` | ✅ | `?cliente_id=X` | `List[ContestacaoOut]` |
| GET | `/contestacoes/{id}` | ✅ | — | `ContestacaoOut` |
| PUT | `/contestacoes/{id}/status` | ✅ | `{"status": "enviada"}` | `ContestacaoOut` |
| POST | `/contestacoes/{id}/save-edit` | ✅ | `{"html": "..."}` | `ContestacaoOut` |
| GET | `/contestacoes/{id}/download` | ✅ | `?format=pdf\|html` | `FileResponse` |
| DELETE | `/contestacoes/{id}` | ✅ | — | `{"ok": true}` |
| GET | `/relatorios/tasks/{id}/download` | ✅ | `?format=pdf\|html` | `FileResponse` *(modificar existente)* |
| GET | `/abusividade/tasks/{id}/download` | ✅ | `?format=pdf\|html` | `FileResponse` *(modificar existente)* |
| POST | `/ia/chat` | ✅ | `ChatRequest` | `ChatResponse` |
| GET | `/notificacoes` | ✅ | `?limit=20&offset=0` | `List[NotificacaoOut]` |
| GET | `/notificacoes/nao-lidas/count` | ✅ | — | `{"count": int}` |
| PUT | `/notificacoes/{id}/lida` | ✅ | — | `NotificacaoOut` |
| PUT | `/notificacoes/marcar-todas-lidas` | ✅ | — | `{"updated": int}` |
| DELETE | `/notificacoes/{id}` | ✅ | — | `{"ok": true}` |

---

## 4. Contratos de Dados — Novos Models

### `TaxaContratada` — Story 3.11

| Campo | Tipo SQL | Nullable | Notas |
|-------|----------|----------|-------|
| `id` | `INTEGER PK AUTOINCREMENT` | não | |
| `cliente_id` | `INTEGER FK(clientes.cliente_id)` | não | index |
| `bandeira` | `VARCHAR(50)` | não | ex: VISA, MASTER, ELO |
| `modalidade` | `VARCHAR(50)` | não | ex: credito, debito, parcelado |
| `taxa_contratada` | `NUMERIC(10,4)` | não | percentual — 4 casas decimais |
| `vigencia_ini` | `DATE` | não | início da vigência contratual |
| `vigencia_fim` | `DATE` | sim | NULL = vigente atualmente |
| `observacao` | `VARCHAR(500)` | sim | |
| `criado_em` | `TIMESTAMP` | não | default=now |
| `atualizado_em` | `TIMESTAMP` | não | onupdate=now |

> ⚠️ **Atenção:** Não confundir com o model `Taxa` existente (taxas de referência por EC/bandeira). São entidades distintas com propósitos diferentes.

### `Contestacao` — Story 3.12

| Campo | Tipo SQL | Nullable | Notas |
|-------|----------|----------|-------|
| `id` | `INTEGER PK AUTOINCREMENT` | não | |
| `cliente_id` | `INTEGER FK(clientes.cliente_id)` | não | index |
| `processamento_id` | `VARCHAR(100)` | não | FK fraca (processamento pode ser legado) |
| `adquirente` | `VARCHAR(100)` | não | |
| `periodo_inicio` | `DATE` | não | |
| `periodo_fim` | `DATE` | não | |
| `status` | `VARCHAR(30)` | não | `rascunho`\|`enviada`\|`em_analise`\|`deferida`\|`indeferida` |
| `html_carta` | `TEXT` | sim | gerado por Jinja2; pode ser editado pelo usuário |
| `desvios_json` | `TEXT` | sim | snapshot JSON de `List[DesvioTaxa]` no momento da geração |
| `valor_excesso_total` | `NUMERIC(15,2)` | sim | calculado de desvios |
| `created_by` | `VARCHAR(100)` | não | login do usuário |
| `criado_em` | `TIMESTAMP` | não | default=now |
| `atualizado_em` | `TIMESTAMP` | não | onupdate=now |

### `Notificacao` — Story 3.15

| Campo | Tipo SQL | Nullable | Notas |
|-------|----------|----------|-------|
| `id` | `INTEGER PK AUTOINCREMENT` | não | |
| `usuario_id` | `INTEGER FK(usuarios.id)` | não | index |
| `tipo` | `VARCHAR(50)` | não | ver enum abaixo |
| `titulo` | `VARCHAR(200)` | não | |
| `mensagem` | `VARCHAR(500)` | não | |
| `link` | `VARCHAR(500)` | sim | rota frontend ex: `/contestacoes/123` |
| `lida` | `BOOLEAN` | não | default=False |
| `criado_em` | `TIMESTAMP` | não | index — ordenação |

**Enum `tipo` para Notificacao:**
`importacao_ok` | `importacao_erro` | `calculo_ok` | `relatorio_ok` | `abusividade_detectada` | `extrato_divergente` | `contestacao_gerada`

### Schemas Pydantic críticos

```python
# Story 3.11
class DesvioTaxa(BaseModel):
    bandeira: str
    modalidade: str
    taxa_contratada: float
    taxa_media_cobrada: float
    desvio_percentual: float      # ((cobrada - contratada) / contratada) * 100
    valor_total_transacoes: float
    valor_excesso_estimado: float # valor_total * (desvio / 100) se desvio > 0
    status: Literal["ok", "atencao", "abusivo"]
    quantidade_transacoes: int

# Story 3.10
class DashboardResumo(BaseModel):
    total_clientes: int
    processamentos_mes: int
    valor_total_analisado: float
    alertas_abusividade: int
    contestacoes_abertas: int      # status não in ('deferida', 'indeferida')
    extratos_divergentes: int
    economia_identificada: float   # soma valor_excesso_total de contestações

# Story 3.14
class ChatRequest(BaseModel):
    mensagem: str
    processamento_id: Optional[str] = None
    cliente_id: Optional[int] = None
    historico: List[dict] = []     # [{"role": "user"|"assistant", "content": "..."}]

class ChatResponse(BaseModel):
    resposta: str
    dados_contexto: Optional[dict] = None
    sugestoes: List[str] = []
```

---

## 5. Decisões Técnicas Obrigatórias

### PDF: WeasyPrint (não Playwright)

```python
# apps/api/app/services/pdf_service.py
class PdfService:
    @staticmethod
    def html_to_pdf(html_content: str) -> bytes:
        from weasyprint import HTML
        import io
        buffer = io.BytesIO()
        HTML(string=html_content).write_pdf(buffer)
        return buffer.getvalue()
```

**Constraint:** CSS dos templates deve ser **inline** ou `<style>` interno — sem CDN externo (WeasyPrint não acessa internet).

### Notificações: Polling 30s (não WebSocket)

WebSocket requer estado de conexão persistente — incompatível com o padrão stateless atual. Revisar em Sprint 5 se volume justificar.

```typescript
// apps/web/src/hooks/useNotificacoesCount.ts
useEffect(() => {
  const poll = () => fetch('/api/notificacoes/nao-lidas/count').then(r => r.json()).then(d => setCount(d.count));
  poll();
  const interval = setInterval(poll, 30000);
  return () => clearInterval(interval);
}, []);
```

**Index obrigatório:** `CREATE INDEX idx_notif_usuario_lida ON notificacoes(usuario_id, lida, criado_em DESC)` — garante performance do polling.

### Injeção de NotificacaoService — padrão opcional

```python
# Para não quebrar testes existentes — sempre opcional
def processar(self, task_id: str, db: Session, usuario_id: Optional[int] = None):
    # ... lógica existente ...
    if usuario_id:
        NotificacaoService.criar(db, usuario_id, "calculo_ok", ...)
```

### Rate Limiting IA — dict em memória (MVP)

```python
from collections import defaultdict
from datetime import datetime, timedelta

_ia_requests: dict = defaultdict(list)

def check_rate_limit(user_id: int, max_per_min: int = 10) -> bool:
    now = datetime.utcnow()
    cutoff = now - timedelta(minutes=1)
    _ia_requests[user_id] = [t for t in _ia_requests[user_id] if t > cutoff]
    if len(_ia_requests[user_id]) >= max_per_min:
        return False
    _ia_requests[user_id].append(now)
    return True
```

### Template Contestação — diretório

Arquivo `template_contestacao.html` vai em `apps/api/app/templates/` (verificar se diretório existe; se não, criar). `ContestacaoService` usa `jinja2.Environment(loader=FileSystemLoader("app/templates/"))`.

---

## 6. Riscos e Mitigações

| Risco | Prob | Impacto | Mitigação |
|-------|------|---------|-----------|
| `TaxaContratada` confundida com `Taxa` existente | Alta | Médio | Tabela `taxas_contratadas` (plural+contratadas) — nome distinto; documentar diferença no model |
| WeasyPrint falha com CSS complexo dos templates | Média | Alto | CSS deve ser inline. Smoke test de PDF no CI: verificar bytes > 0 e header `%PDF` |
| Polling sobrecarregar DB em produção | Baixa | Médio | Index `(usuario_id, lida, criado_em)`. Cache de count por 10s se necessário |
| `ai_service.py` existente incompatível | Média | Alto | **Ler arquivo antes de implementar 3.14** — adaptar interface, não recriar |
| 3.15 injetando em services existentes quebrar testes | Alta | Médio | Usar parâmetro `usuario_id: Optional[int] = None` — chamada só ocorre quando fornecido |
| `html_carta` muito grande | Baixa | Baixo | TEXT no SQLite/PG não tem limite prático |

---

## 7. Arquivos Modificados por Story

| Story | Arquivo | Tipo |
|-------|---------|------|
| 3.10 | `apps/api/app/api/v1/api.py` | Adicionar router dashboard |
| 3.10 | `apps/web/src/app/(dashboard)/page.tsx` | Substituir home atual |
| 3.10 | `apps/web/src/components/layout/Sidebar.tsx` | Adicionar item Dashboard |
| 3.11 | `apps/api/app/models/__init__.py` | Exportar TaxaContratada |
| 3.12 | `apps/api/app/api/v1/api.py` | Adicionar router contestações |
| 3.13 | `apps/api/app/api/v1/endpoints/relatorios.py` | Adicionar `?format=` no download |
| 3.13 | `apps/api/app/api/v1/endpoints/abusividade.py` | Adicionar `?format=` no download |
| 3.14 | `apps/api/app/services/ai_service.py` | Estender com `montar_contexto()` e rate limit |
| 3.14 | `apps/api/app/api/v1/endpoints/ai.py` | Adicionar `POST /ia/chat` |
| 3.15 | `apps/api/app/services/relatorio_service.py` | Injetar NotificacaoService |
| 3.15 | `apps/api/app/services/calculo_service.py` | Injetar NotificacaoService |
| 3.15 | `apps/api/app/services/import_service.py` | Injetar NotificacaoService |
| 3.15 | `apps/api/app/services/abusividade_service.py` | Injetar NotificacaoService |
| 3.15 | `apps/web/src/app/layout.tsx` (ou header) | Adicionar NotificacoesSino |

---

## 8. Arquivo de referência de padrões

Para implementar os novos models, usar `apps/api/app/models/taxa.py` como referência de convenção de colunas, nomenclatura e timestamps.

Para registrar novos routers, seguir o padrão em `apps/api/app/api/v1/api.py`.

---

*Documento gerado por @architect (Aria) — Sprint 4 — 2026-03-20*
