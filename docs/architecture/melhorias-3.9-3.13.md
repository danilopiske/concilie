# Melhorias Técnicas — Stories 3.9 e 3.13

## 3.9 Abusividade — Logging e Performance

### Logging

**Problema:** `print()` em vez de logger estruturado em paths críticos.

- `abusividade_service.py` linha ~123-126: `except Exception` com `print()`
- `abusividade_relatorio_service.py` linha ~135-139: mesmo padrão

**Correção:**
```python
import logging
logger = logging.getLogger(__name__)

# Antes:
except Exception as e:
    print(f"Erro: {e}")

# Depois:
except Exception as e:
    logger.error("Erro ao processar abusividade", exc_info=True, extra={"calc_id": calc_id})
```

### Performance — N+1 Queries

**Problema:** Query por processamento sem join; sem índices em colunas de filtro.

- `abusividade_service.py` linha ~44-45: loop com query individual
- `analisar_detalhado()`: raw SQL sem índice hints

**Índices sugeridos (migration):**
```sql
CREATE INDEX idx_vendas_calculos_filter
  ON vendas_calculos(calc_id, data_venda, bandeira, forma_pagamento);
```

### Error Handling

- Linha ~206-209: retorna resposta vazia sem logar causa raiz
- Divisão por zero em `media_geral`: verificação inconsistente

---

## 3.13 PDF — Retry Logic e CSS de Impressão

### Retry Logic

**Problema:** Falha imediata no `WeasyPrint` sem retentativas; sem timeout.

```python
# Antes (pdf_service.py):
try:
    pdf = HTML(string=html).write_pdf()
except Exception as e:
    raise

# Depois (com retry e timeout):
import time

def gerar_pdf_com_retry(html: str, tentativas: int = 3, timeout: int = 30) -> bytes:
    for i in range(tentativas):
        try:
            return HTML(string=html).write_pdf(presentational_hints=True)
        except Exception as e:
            if i == tentativas - 1:
                logger.error("PDF falhou após %d tentativas", tentativas, exc_info=True)
                raise
            logger.warning("Tentativa %d falhou, retentando...", i + 1)
            time.sleep(2 ** i)  # backoff exponencial
```

### CSS de Impressão

**Problema:** HTMLs gerados sem `@media print` — layout quebra em múltiplas páginas.

**CSS sugerido (adicionar nos templates):**
```css
@media print {
  body { margin: 0; font-size: 12px; }
  table { page-break-inside: avoid; }
  .page-break { page-break-before: always; }
  thead { display: table-header-group; }
  tfoot { display: table-footer-group; }
}
```

### Memory

**Problema:** `BytesIO` não liberado explicitamente; PDFs grandes ficam inteiros em memória.

```python
# Usar context manager:
from io import BytesIO
buf = BytesIO()
try:
    HTML(string=html).write_pdf(buf)
    return buf.getvalue()
finally:
    buf.close()
```

---

## Prioridade de Implementação

| Item | Severidade | Impacto |
|------|-----------|---------|
| Índices `vendas_calculos` | ALTA | Queries escalam O(n), >100ms em datasets grandes |
| Logging estruturado | ALTA | Debug em produção impossível sem rastreamento |
| Retry PDF | MÉDIA | Falhas transitórias causam erro para o usuário |
| CSS impressão | MÉDIA | Layout quebra em relatórios multi-página |
| Timeout PDF | MÉDIA | Arquivos grandes podem travar worker indefinidamente |
