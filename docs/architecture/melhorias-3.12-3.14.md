# Melhorias Técnicas — Stories 3.12 e 3.14

## 3.12 Contestação — Normalização

### 1. Status sem Enum
Campo `status` aceita qualquer string — sem validação de domínio.
```python
# Antes (model):
status = Column(String, default="aberta")

# Depois:
from enum import Enum as PyEnum
class StatusContestacao(str, PyEnum):
    aberta = "aberta"
    em_analise = "em_analise"
    resolvida = "resolvida"
    improcedente = "improcedente"

status = Column(SQLAlchemyEnum(StatusContestacao), default=StatusContestacao.aberta)
```

### 2. Datas sem Timezone
`periodo_inicio` e `periodo_fim` usam `Date` sem timezone — risco de off-by-one em fusos.
```python
# Antes:
periodo_inicio = Column(Date)

# Depois:
from sqlalchemy import DateTime
periodo_inicio = Column(DateTime(timezone=True))
```

### 3. Duplicação de HTML (DB + disco)
HTML salvo em banco e em arquivo — dessincronização silenciosa se um falhar.

**Solução:** centralizar em DB apenas ou usar S3 com referência no DB.
```python
# Manter apenas no DB:
html_carta = Column(Text, nullable=True)
# remover lógica de escrita em disco do service
```

### 4. Sem validação de período
`periodo_fim < periodo_inicio` é aceito sem erro.
```python
# No schema Pydantic:
@validator('periodo_fim')
def fim_apos_inicio(cls, v, values):
    if 'periodo_inicio' in values and v < values['periodo_inicio']:
        raise ValueError('periodo_fim deve ser >= periodo_inicio')
    return v
```

### 5. Timestamps inconsistentes no schema
Resposta mistura formatos ISO — padronizar com `datetime` tipado.
```python
class ContestacaoResponse(BaseModel):
    created_at: datetime
    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}
```

---

## 3.14 IA Chat — Rate Limiting e Resiliência

### 1. Rate limiting em memória (não persistido)
Reseta no restart do servidor — não funciona com múltiplos workers.
```python
# Antes: dict in-memory
rate_limit_store = {}

# Depois: usar Redis
import redis
r = redis.Redis(host=settings.REDIS_HOST, decode_responses=True)

def check_rate_limit(user_id: str, max_req: int = 10, window: int = 60) -> bool:
    key = f"ia_rate:{user_id}"
    count = r.incr(key)
    if count == 1:
        r.expire(key, window)
    return count <= max_req
```

### 2. Sem contagem de tokens
Histórico enviado ao Gemini sem verificar limite de context window.
```python
import tiktoken  # ou usar contagem aproximada

MAX_TOKENS = 30_000

def truncar_historico(messages: list, max_tokens: int = MAX_TOKENS) -> list:
    total = 0
    resultado = []
    for msg in reversed(messages):
        tokens = len(msg["content"].split()) * 1.3  # aproximação
        if total + tokens > max_tokens:
            break
        resultado.insert(0, msg)
        total += tokens
    return resultado
```

### 3. Sem retry / fallback na API
Falha da API Gemini retorna erro genérico sem recuperação.
```python
import time

def chamar_gemini_com_retry(prompt: str, tentativas: int = 3) -> str:
    for i in range(tentativas):
        try:
            return gemini_client.generate_content(prompt).text
        except Exception as e:
            if i == tentativas - 1:
                logger.error("Gemini falhou após %d tentativas", tentativas, exc_info=True)
                return "Serviço temporariamente indisponível. Tente novamente em instantes."
            time.sleep(2 ** i)
```

### 4. Histórico ilimitado no frontend
Mensagens acumulam indefinidamente — memória e tokens crescem sem controle.
```python
# No endpoint backend — limitar antes de enviar:
MAX_HISTORY = 20
messages = messages[-MAX_HISTORY:]
```

### 5. Sem timeout na chamada API
`send_message()` pode travar o worker indefinidamente.
```python
import asyncio

async def chamar_gemini_timeout(prompt: str, timeout: int = 30) -> str:
    try:
        return await asyncio.wait_for(
            asyncio.to_thread(gemini_client.generate_content, prompt),
            timeout=timeout
        )
    except asyncio.TimeoutError:
        raise HTTPException(status_code=504, detail="IA demorou demais. Tente novamente.")
```

### 6. Dados indisponíveis sem contexto
Quando `VendasCalculos` está vazia, retorna mensagem genérica sem indicar o motivo.
```python
if not vendas:
    return {"resposta": "Não há dados de vendas disponíveis para o período selecionado. Importe processamentos primeiro."}
```

---

## Prioridade de Implementação

| Item | Story | Severidade | Impacto |
|------|-------|-----------|---------|
| Rate limiting Redis | 3.14 | ALTA | Multi-worker sem proteção |
| Contagem de tokens | 3.14 | ALTA | Overflow silencioso na API |
| Status com Enum | 3.12 | ALTA | Dados inválidos no banco |
| Retry Gemini | 3.14 | MÉDIA | UX — erro em falhas transitórias |
| Validação período | 3.12 | MÉDIA | Dados incoerentes |
| Timeout API | 3.14 | MÉDIA | Worker travado |
| HTML duplicado | 3.12 | MÉDIA | Dessincronização silenciosa |
| Histórico ilimitado | 3.14 | BAIXA | Degradação gradual de performance |
