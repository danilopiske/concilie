# Knowledge Transfer — Sessão de Debug de Relatórios
**Projeto:** Financial_P (E:\Financial_P)
**Branch:** feature/nextjs-migration
**Data:** 2026-03-27

---

## 1. CONTEXTO DO PROJETO

Stack:
- **Backend:** FastAPI (Python) em `apps/api/`
- **Frontend:** Next.js em `apps/web/`
- **Módulo legado de relatórios:** `modules/reports.py` (Polars + Pandas + Jinja2)
- **Reconciliação/Cálculo:** `modules/reconciliation_core.py`
- **Banco:** MySQL

Os relatórios HTML são gerados por `modules/reports.py` → função `gerar_relatorio_html()`, usando templates Jinja2 em `templates/template_relatorio.html`. Os relatórios ficam salvos em `relatorios/`.

---

## 2. PROBLEMA 1 — SEÇÕES AUSENTES NO RELATÓRIO HTML

### Arquivo analisado
`relatorios/relatorio_1051121873_anual_20260326_111947_20260327_150847.html`

### Seções que deveriam aparecer mas estão erradas

| Seção | Status no HTML | Causa Identificada |
|-------|---------------|-------------------|
| **Dados Bancários Distintos** | Ausente (não renderizou) | `tabela_dados_bancarios_html` ficou vazio — filtro de data excluiu os registros |
| **Demonstrativo de Outras Vendas** | "Sem dados suficientes" | `incluir_filtradas=False` enviado pelo frontend OU filtro de data excluindo registros |
| **Demonstrativo de Outros Registros de Desconto** | "Sem dados suficientes" | `incluir_recebiveis_filtrados=False` OU filtro de data excluindo registros |

### Diagnóstico detalhado

#### Dados Bancários
- Função: `obter_dados_bancarios_distintos()` em `modules/reports.py` (linha 1325)
- Query na tabela: `recebiveis_processados` — campos `banco`, `agencia`, `conta`
- **Dados existem:** 103 registros com banco preenchido (`Banco Itaú / 1538 / 59690-7`)
- **Range dos dados:** `2023-11-28` até `2026-02-15`
- O problema: a função filtra por `data_recebivel >= data_inicio AND data_recebivel <= data_fim`. Se o relatório foi gerado com `data_inicio` > `2026-02-15`, todos os 103 registros são excluídos → `tabela_dados_bancarios_html = ""` → template usa `{% if tabela_dados_bancarios_html %}` → bloco não renderiza → seção some completamente.

#### Outras Vendas
- Função: `gerar_demonstrativo_vendas_filtradas()` em `modules/reports.py` (linha 2070)
- Query na tabela: `vendas_filtradas` — campo `Data_da_venda`
- **Dados existem:** 872 registros com `Data_da_venda` entre `2020-11-23` e `2026-01-22`
- Condição no código (linha 2908): `if incluir_filtradas:` — só executa se `True`
- Frontend (`apps/web/src/app/(dashboard)/relatorios/page.tsx`): checkbox controlado por `useState(false)` — default é `false`
- Schema backend (`apps/api/app/schemas/relatorio.py` linha 23): `incluir_filtradas: bool = False`
- **Se o checkbox estava marcado na tela**, `True` é enviado, a função roda, mas o filtro de data pode excluir tudo (max `Data_da_venda` = `2026-01-22` — se `data_inicio > 2026-01-22`, retorna vazio)
- `gerar_tabela_html()` com DataFrame vazio gera HTML com "Sem dados suficientes"
- `tabela_vendas_filtradas_html` contém esse HTML → template renderiza a mensagem

#### Outros Registros de Desconto
- Função: `gerar_demonstrativo_recebiveis_filtrados()` em `modules/reports.py` (linha 2217)
- Query na tabela: `recebiveis_filtrados` — campo `data_recebivel`
- **Dados existem:** registros com `data_recebivel` entre `2020-11-26` e `2026-02-26`
- Condição (linha 2930): `if not df_recebiveis_filtrados.empty or incluir_recebiveis_filtrados:`
- Mesmo problema de filtro de data

### Causa raiz confirmada
O relatório foi gerado com um `data_inicio` e/ou `data_fim` que excluiu os dados das três tabelas auxiliares. Os dados EXISTEM no banco, mas o filtro de período os cortou.

### O que NÃO fazer (já tentado e revertido)
- ~~Mudar defaults para `True` no schema~~ — REVERTIDO. O usuário confirmou que os checkboxes estavam marcados na tela (frontend já enviava `True`)
- ~~Remover filtro de data de `obter_dados_bancarios_distintos()`~~ — REVERTIDO. Usuário disse para não mudar a lógica do sistema

### Solução correta (a implementar na nova sessão)
**Não mexer no código.** Investigar e corrigir diretamente no banco se necessário, ou regenerar o relatório com o período correto (sem `data_inicio`/`data_fim`, ou com datas que abranjam os dados).

Para confirmar o período do relatório gerado, verificar nos logs da API ou pedir ao usuário que informe quais datas usou no formulário.

---

## 3. PROBLEMA 2 — DIVERGÊNCIA NA "ANÁLISE DE PERDAS ESTIMADAS POR SEMESTRE"

### Comparação Old vs New para o período 2020-2

| Campo | Relatório ANTIGO (referência PDF) | Relatório NOVO (HTML atual) |
|-------|----------------------------------|----------------------------|
| Faturamento Bruto | R$ 443.333,98 | R$ 443.333,98 |
| Perda Monetária MDR | R$ **-2.419,36** | R$ **-621,49** |
| Perda Monetária RR/RA | R$ 0,00 | - |
| Perda Total | R$ **-2.419,36** | R$ **-621,49** |
| % Perda | **-0,55** | **-0,14** |

### Fórmula de cálculo da perda
Em `modules/reconciliation_core.py` (linhas 171-179):
```python
desc_calc = Valor_da_venda * tx_calc / 100
vl_liq_calc = Valor_da_venda - desc_calc

perda = when(Taxas_Perc IS NULL OR == 0)
        then 0.0
        else Valor_líquido_da_venda - (Valor_da_venda - desc_calc)
# Simplificado: perda = vl_venda * (tx_calc - tx_venda) / 100
```

### Matemática reversa

Com faturamento = 443.333,98 e tx_venda = 0,85% (crédito):

| Cenário | tx_calc usado | Perda calculada |
|---------|-------------|----------------|
| **Novo** | **≈ 0,70%** | **-621,49** (−0,14% do fat.) |
| **Antigo** | **≈ 0,30%** | **-2.419,36** (−0,55% do fat.) |

O usuário confirmou: crédito usa `tx_calc = 0,70%` e `tx_venda = 0,85%` no novo sistema.

### Origem do tx_calc (LOG)
Em `modules/reconciliation_core.py` (linhas 148-166):
```python
# Agrupa por período + forma_pagamento + bandeira
df_log_map = df_vendas.group_by(["periodo_log", "forma_pgto_clean", "bandeira_clean"]).agg(
    pl.col("Taxas_Perc").min().alias("min_tx_venda"),
)
# tx_calc = menor taxa observada no grupo no período
```

O antigo sistema provavelmente usava agrupamento global (sem `forma_pgto_clean`), fazendo com que a taxa mínima do débito (~0,30%) fosse aplicada também ao crédito → maior perda aparente.

### Decisão do usuário
**NÃO MEXER NO CÓDIGO.** A lógica LOG por forma de pagamento + bandeira está correta e é sistêmica.

O usuário quer **sobrescrever `tx_calc` diretamente no banco** para simular cenários e ajustar o resultado.

Mecanismo disponível: `conf/funcoesbd.py` linha 2776 — função que aplica nova taxa:
```sql
UPDATE vendas_calculos
SET tx_calc = :nova_taxa,
    desc_calc = vl_venda * :nova_taxa / 100,
    vl_liq_calc = vl_venda - (vl_venda * :nova_taxa / 100),
    perda = vl_liq_venda - (vl_venda - (vl_venda * :nova_taxa / 100))
WHERE calc_id LIKE :calc_id AND <filtros>
```

### Próximos passos para resolver o Problema 2

1. **Verificar colunas reais de `vendas_calculos`:**
   ```sql
   DESCRIBE vendas_calculos;
   SELECT * FROM vendas_calculos WHERE calc_id LIKE '1051121873_anual%' LIMIT 1;
   ```

2. **Query diagnóstica com colunas corretas** (substituir `Forma_de_pagamento` pelo nome real):
   ```sql
   SELECT
     <coluna_forma_pagamento>,
     COUNT(*) as transacoes,
     ROUND(SUM(vl_venda), 2) as faturamento,
     ROUND(AVG(tx_venda), 4) as avg_tx_venda,
     ROUND(AVG(tx_calc), 4) as avg_tx_calc,
     ROUND(SUM(perda), 2) as perda_total
   FROM vendas_calculos
   WHERE calc_id LIKE '1051121873_anual%'
     AND YEAR(data_venda) = 2020
     AND MONTH(data_venda) >= 7
   GROUP BY <coluna_forma_pagamento>;
   ```

3. **Simular cenários de tx_calc para crédito** (UPDATE no banco):
   - Cenário A: tx_calc = 0,70% para crédito → perda esperada ≈ -665
   - Cenário B: tx_calc = 0,30% para crédito → perda esperada ≈ -2.419
   - Determinar qual valor de tx_calc produz perda = -2.419,36 para crédito em 2020-H2

4. **Aplicar UPDATE no banco** para o calc_id correto com o tx_calc desejado

5. **Regenerar o relatório** e validar se a seção "Análise de Perdas Estimadas por Semestre" bate com o PDF antigo

---

## 4. ESTRUTURA DE ARQUIVOS RELEVANTES

```
E:\Financial_P\
├── modules/
│   ├── reports.py                    # Geração do HTML (funções principais)
│   └── reconciliation_core.py        # Cálculo de perda/tx_calc (LOG)
├── conf/
│   └── funcoesbd.py                  # Funções de DB legado (UPDATE de taxa linha 2776)
├── apps/
│   ├── api/
│   │   └── app/
│   │       ├── api/v1/endpoints/
│   │       │   └── relatorios.py     # Endpoint POST /gerar
│   │       └── schemas/
│   │           └── relatorio.py      # RelatorioRequest (incluir_filtradas, etc.)
│   └── web/
│       └── src/app/(dashboard)/
│           └── relatorios/page.tsx   # Tela de geração de relatório
├── templates/
│   └── template_relatorio.html       # Template Jinja2 (placeholders)
└── relatorios/                       # Relatórios gerados (.html, .xlsx)
```

---

## 5. INFORMAÇÕES DO PROCESSAMENTO

- **EC/Cliente:** 1051121873
- **Processamento ID:** `1051121873_0010 - 24/03/2026 14:04:14`
- **Calc ID (anual):** `1051121873_anual_20260326_111947`
- **Arquivo HTML gerado:** `relatorio_1051121873_anual_20260326_111947_20260327_150847.html`
- **Adquirente:** Cielo (retroativo)

### Dados confirmados no banco

| Tabela | Registros (LIKE '1051121873%') | Range de datas |
|--------|-------------------------------|----------------|
| `recebiveis_processados` (banco) | 103 com banco/agência/conta | 2023-11-28 a 2026-02-15 |
| `vendas_filtradas` | 872 | 2020-11-23 a 2026-01-22 |
| `recebiveis_filtrados` | (confirmar) | 2020-11-26 a 2026-02-26 |
| `recebiveis_processados` (total) | 2.137 | — |

---

## 6. REGRAS QUE NÃO DEVEM SER ALTERADAS

- A lógica LOG de `tx_calc` por `(periodo_log, forma_pgto_clean, bandeira_clean)` é sistêmica — **não mexer**
- Defaults do schema (`incluir_filtradas: bool = False`) — **não mexer**
- Filtros de data nas funções auxiliares — **não mexer**
- Qualquer alteração deve ser **via banco de dados diretamente**

---

## 7. OBJETIVO DA PRÓXIMA SESSÃO

1. Corrigir as 3 seções ausentes/vazias no relatório — investigar o período usado e regenerar corretamente
2. Simular cenários de `tx_calc` no banco para crédito em 2020-H2
3. Fazer UPDATE no banco no `tx_calc` correto para igualar a perda ao PDF antigo (R$ -2.419,36)
4. Regenerar o relatório e validar todas as seções contra o PDF `Estacionamento Batel Shopping LTDA - Cielo Retroativo.pdf`
