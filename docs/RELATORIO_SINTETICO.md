# Relatório Sintético - Guia de Estrutura e Formato

## 📋 Visão Geral

O **Relatório Sintético** é uma versão simplificada e executiva do relatório de conciliação financeira, projetada para clientes leigos ou gestores que necessitam de uma visão rápida e clara dos resultados, sem detalhes técnicos excessivos.

**Diferenças principais:**

| Aspecto | Relatório Analítico (Atual) | Relatório Sintético (Proposto) |
|---------|----------------------------|----------------------------------|
| **Público-alvo** | Analistas financeiros, auditores | Gestores, clientes não-técnicos |
| **Formato** | Tabelas detalhadas + gráficos técnicos | Texto narrativo + KPIs visuais |
| **Tamanho** | 8-15 páginas (com anexos) | 2-4 páginas |
| **Dados apresentados** | Todas as transações com evidências | Resumo executivo com destaques |
| **Linguagem** | Técnica (taxas MDR, recebíveis, etc.) | Simples (valores, perdas, taxas médias) |

---

## 🎯 Estrutura Proposta do Relatório Sintético

### **1. Cabeçalho Executivo**
```
===========================================
      RELATÓRIO SINTÉTICO DE CONCILIAÇÃO
          Período: Janeiro/2025
           Cliente: [Nome da Empresa]
===========================================
```

**Conteúdo:**
- Nome do cliente
- Período analisado (ex: "01/01/2025 a 31/01/2025")
- Data de geração do relatório
- Adquirente(s) processada(s) (ex: "Cielo, Rede, Stone")

---

### **2. Resumo do Faturamento (Parágrafo Descritivo)**

**Exemplo de texto:**

> No período de **01/01/2025 a 31/01/2025**, foram processadas **1.243 transações** via cartão de crédito e débito, totalizando um **faturamento bruto de R$ 456.789,50**. Após descontos de taxas das operadoras, o **valor líquido recebido** foi de **R$ 442.310,25**, representando **96,83% do faturamento**.

**Dados apresentados:**
- Quantidade total de transações
- Faturamento bruto (soma das vendas)
- Valor líquido (após taxas)
- Percentual líquido (valor líquido / faturamento bruto)

---

### **3. Indicadores Principais (KPIs Visuais)**

Apresentação em **cartões destacados** (boxes coloridos no HTML):

```
┌──────────────────────────┬──────────────────────────┬──────────────────────────┐
│   💰 TICKET MÉDIO        │   📊 TAXA MÉDIA          │   ⚠️ DIVERGÊNCIAS         │
│   R$ 367,45              │   3,17%                  │   R$ 14.479,25           │
│   (por transação)        │   (taxas aplicadas)      │   (perdas estimadas)     │
└──────────────────────────┴──────────────────────────┴──────────────────────────┘
```

**Dados exibidos:**
- **Ticket Médio:** Valor médio por transação (faturamento bruto / quantidade)
- **Taxa Média:** Taxa percentual média cobrada pelas operadoras
- **Divergências:** Soma das perdas identificadas (diferença entre taxa cadastrada vs. taxa aplicada)

---

### **4. Análise por Bandeira (Tabela Simplificada)**

**Exemplo:**

| Bandeira | Transações | Faturamento | % do Total |
|----------|-----------|-------------|-----------|
| Visa | 587 | R$ 201.450,30 | 44,1% |
| Mastercard | 412 | R$ 168.920,15 | 37,0% |
| Elo | 189 | R$ 64.319,05 | 14,1% |
| Amex | 55 | R$ 22.100,00 | 4,8% |

**Objetivo:** Mostrar distribuição do faturamento por bandeira de forma clara.

---

### **5. Destaques do Período (Parágrafo + Lista)**

**Exemplo de texto:**

> Durante a análise, foram identificados os seguintes **pontos de atenção**:

- ✅ **Taxa média dentro do esperado:** A taxa aplicada (3,17%) está alinhada com o contrato de 3,15% ± 0,05%.
- ⚠️ **Divergências detectadas:** 78 transações apresentaram taxas acima do contratado, gerando perda de R$ 14.479,25.
- 📈 **Crescimento:** Houve aumento de 12,5% no faturamento em relação ao mês anterior.
- 🔍 **Transações suspeitas:** 3 transações com valores extremos (>R$ 10.000) identificadas para revisão.

**Dados apresentados:**
- Conformidade de taxas (sim/não)
- Quantidade de divergências encontradas
- Comparação com período anterior (se disponível)
- Alertas de transações atípicas (valores muito altos ou muito baixos)

---

### **6. Evidências Selecionadas (Top 3 Apenas)**

**Tabela compacta:**

#### 🔺 3 Maiores Valores Processados

| Data | Bandeira | Valor | Taxa Aplicada |
|------|----------|-------|---------------|
| 15/01/2025 | Visa | R$ 15.600,00 | 3,25% |
| 22/01/2025 | Mastercard | R$ 12.300,50 | 3,18% |
| 28/01/2025 | Elo | R$ 10.890,00 | 3,45% |

**Objetivo:** Mostrar apenas as transações mais relevantes para revisão manual, sem NSU ou códigos técnicos.

---

### **7. Conclusão e Recomendações (Texto Livre)**

**Exemplo:**

> **Conclusão:**  
> A conciliação do período apresentou **boa conformidade geral**, com apenas **6,27% de transações com divergências**. As perdas identificadas (R$ 14.479,25) representam **3,17% do faturamento**, valor considerado aceitável dentro da margem de negociação.

> **Recomendações:**
> 1. Revisar as 3 transações com valores acima de R$ 10.000 diretamente com a adquirente.
> 2. Solicitar renegociação de taxa para bandeira Elo (taxa média de 3,45% vs. contrato de 3,15%).
> 3. Acompanhar comportamento do próximo mês para validar tendência de crescimento.

---

## 🛠️ Implementação Técnica

### **Formato de Saída**
- **HTML:** Template Jinja2 com CSS embutido, sem gráficos (apenas ícones e cartões)
- **PDF (opcional):** Conversão do HTML via WeasyPrint ou wkhtmltopdf
- **Email:** Corpo do relatório em HTML inline (compatível com Outlook/Gmail)

### **Dados Necessários (do banco de dados)**
```python
dados_sintetico = {
    "total_transacoes": 1243,
    "faturamento_bruto": 456789.50,
    "valor_liquido": 442310.25,
    "ticket_medio": 367.45,
    "taxa_media": 3.17,
    "total_divergencias": 14479.25,
    "qtd_divergencias": 78,
    "bandeiras": [
        {"nome": "Visa", "qtd": 587, "valor": 201450.30, "percentual": 44.1},
        # ...
    ],
    "top_valores": [
        {"data": "15/01/2025", "bandeira": "Visa", "valor": 15600.00, "taxa": 3.25},
        # ...
    ],
    "conformidade_taxa": True,  # taxa média dentro de ±0.05% do contrato
    "transacoes_suspeitas": 3,  # valores > threshold (ex: R$ 10k)
}
```

### **Template Jinja2 (relatorios/template_relatorio_sintetico.html)**
```html
<!DOCTYPE html>
<html>
<head>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; line-height: 1.6; }
        .header { text-align: center; border-bottom: 3px solid #0066cc; padding-bottom: 20px; }
        .kpi-container { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 20px; margin: 30px 0; }
        .kpi-box { background: #f0f8ff; border-left: 4px solid #0066cc; padding: 20px; }
        .kpi-box h3 { margin: 0; color: #0066cc; font-size: 14px; }
        .kpi-box .value { font-size: 28px; font-weight: bold; margin: 10px 0; }
        table { width: 100%; border-collapse: collapse; margin: 20px 0; }
        th { background: #0066cc; color: white; padding: 12px; text-align: left; }
        td { padding: 10px; border-bottom: 1px solid #ddd; }
        .alert { background: #fff3cd; border-left: 4px solid #ffc107; padding: 15px; margin: 20px 0; }
        .success { background: #d4edda; border-left: 4px solid #28a745; padding: 15px; margin: 20px 0; }
    </style>
</head>
<body>
    <div class="header">
        <h1>RELATÓRIO SINTÉTICO DE CONCILIAÇÃO</h1>
        <p><strong>Período:</strong> {{ periodo }} | <strong>Cliente:</strong> {{ cliente }}</p>
    </div>
    
    <div class="kpi-container">
        <div class="kpi-box">
            <h3>💰 TICKET MÉDIO</h3>
            <div class="value">{{ ticket_medio }}</div>
            <small>(por transação)</small>
        </div>
        <div class="kpi-box">
            <h3>📊 TAXA MÉDIA</h3>
            <div class="value">{{ taxa_media }}%</div>
            <small>(taxas aplicadas)</small>
        </div>
        <div class="kpi-box">
            <h3>⚠️ DIVERGÊNCIAS</h3>
            <div class="value">{{ total_divergencias }}</div>
            <small>(perdas estimadas)</small>
        </div>
    </div>
    
    <h2>Resumo do Faturamento</h2>
    <p>{{ resumo_faturamento }}</p>
    
    <h2>Distribuição por Bandeira</h2>
    <table>
        <tr><th>Bandeira</th><th>Transações</th><th>Faturamento</th><th>% do Total</th></tr>
        {% for bandeira in bandeiras %}
        <tr>
            <td>{{ bandeira.nome }}</td>
            <td>{{ bandeira.qtd }}</td>
            <td>{{ bandeira.valor }}</td>
            <td>{{ bandeira.percentual }}%</td>
        </tr>
        {% endfor %}
    </table>
    
    <h2>Destaques do Período</h2>
    <ul>
        {% for destaque in destaques %}
        <li>{{ destaque }}</li>
        {% endfor %}
    </ul>
    
    <h2>Conclusão e Recomendações</h2>
    <p>{{ conclusao }}</p>
    <ul>
        {% for recomendacao in recomendacoes %}
        <li>{{ recomendacao }}</li>
        {% endfor %}
    </ul>
</body>
</html>
```

---

## 📧 Uso Recomendado

### **Quando usar Relatório Sintético:**
- Cliente solicita "resumo rápido" ou "overview"
- Email mensal para gestores (corpo da mensagem)
- Dashboard executivo (apenas números principais)
- Clientes que não têm familiaridade com termos técnicos

### **Quando usar Relatório Analítico:**
- Auditoria completa de conciliação
- Análise detalhada de divergências
- Suporte para contestação junto a adquirentes
- Anexo técnico para contadores/advogados

---

## ✅ Checklist de Implementação

- [ ] Criar função `gerar_relatorio_sintetico()` em `modules/reports.py`
- [ ] Criar template `relatorios/template_relatorio_sintetico.html`
- [ ] Adicionar botão "Gerar Sintético" na UI de relatórios
- [ ] Implementar cálculos de KPIs (ticket médio, taxa média, percentual divergências)
- [ ] Adicionar lógica de "conformidade de taxa" (tolerância ±0.05%)
- [ ] Criar sistema de "destaques automáticos" baseado em regras:
  - Divergências > 5% do faturamento → Alerta
  - Taxa média fora do contrato → Recomendação de renegociação
  - Crescimento/queda > 10% vs. mês anterior → Destaque
- [ ] Testar renderização em diferentes clientes de email (Outlook, Gmail)
- [ ] Adicionar opção de envio automático por email

---

## 🎨 Exemplos Visuais

### **KPI Cards (CSS):**
```css
.kpi-box {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    border-radius: 10px;
    padding: 20px;
    box-shadow: 0 4px 6px rgba(0,0,0,0.1);
}
```

### **Ícones de Status:**
- ✅ Verde: Taxa dentro do esperado
- ⚠️ Amarelo: Divergências < 5% do faturamento
- ❌ Vermelho: Divergências > 5% ou taxa muito fora do contrato

---

## 📊 Exemplo Completo de Saída

```
===========================================
      RELATÓRIO SINTÉTICO DE CONCILIAÇÃO
          Período: Janeiro/2025
          Cliente: Loja Exemplo LTDA
===========================================

No período de 01/01/2025 a 31/01/2025, foram processadas 1.243 
transações via cartão, totalizando um faturamento bruto de 
R$ 456.789,50. Após descontos, o valor líquido foi de R$ 442.310,25 
(96,83% do faturamento).

┌────────────────┬────────────────┬────────────────┐
│ Ticket Médio   │ Taxa Média     │ Divergências   │
│ R$ 367,45      │ 3,17%          │ R$ 14.479,25   │
└────────────────┴────────────────┴────────────────┘

DISTRIBUIÇÃO POR BANDEIRA:
- Visa: 44,1% (R$ 201.450,30)
- Mastercard: 37,0% (R$ 168.920,15)
- Elo: 14,1% (R$ 64.319,05)
- Amex: 4,8% (R$ 22.100,00)

DESTAQUES:
✅ Taxa média dentro do contrato (3,17% vs. 3,15% contratado)
⚠️ 78 transações com divergências (R$ 14.479,25)
📈 Crescimento de 12,5% vs. dezembro/2024

RECOMENDAÇÕES:
1. Revisar 3 transações acima de R$ 10.000
2. Renegociar taxa Elo (3,45% atual vs. 3,15% contrato)

---
Relatório gerado em 01/02/2025 às 14:30
```

---

## 🔗 Integração com Sistema Atual

A função de relatório sintético **deve reutilizar** os dados já processados pelo relatório analítico:

```python
def gerar_relatorio_sintetico(engine, processamento_id, mes_referencia):
    # Reutilizar funções existentes
    metadados = obter_dados_processamento(engine, processamento_id)
    df_vendas = obter_vendas_calculos(engine, processamento_id)
    
    # Calcular KPIs específicos do sintético
    kpis = {
        "ticket_medio": df_vendas["vl_venda"].mean(),
        "taxa_media": df_vendas["tx_venda"].mean(),
        "conformidade": verificar_conformidade_taxa(df_vendas, taxa_contrato=3.15),
        # ...
    }
    
    # Renderizar template sintético
    template = env.get_template("template_relatorio_sintetico.html")
    html_content = template.render(**kpis)
    
    return salvar_relatorio(html_content, "sintetico")
```

---

**Este documento serve como guia para implementação do Relatório Sintético, complementando o Relatório Analítico já existente no sistema.**
