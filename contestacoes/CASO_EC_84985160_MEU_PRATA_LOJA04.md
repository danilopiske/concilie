# Conferência de Taxas — EC 84985160 (Meu Prata Loja 04) — 22/07/2026

**Cliente:** Meu Prata Supermercados LTDA — Meu Prata Loja 04 (cliente_id 16)
**EC:** 84985160
**Adquirente:** Rede
**Processamento analisado:** `84985160_0002 - 16/07/2026 15:04:03` (501.779 linhas, vendas de 02/01/2022 a 31/05/2026)

> Este documento cobre apenas o trabalho de **hoje à noite (22/07/2026)**: análise dos arquivos de conferência enviados pelo funcionário, esclarecimento dos casos que ele apontou, varredura completa das 65 linhas da planilha dele e a decisão sobre "Parcelado Loja". Não inclui correções de bug de sessões anteriores (RR, fallback de taxa zerada), que já estavam aplicadas antes de hoje.

---

## 1. Arquivos recebidos

- `contestacoes/Conferência taxas - - Meu Prata Loja 04.xlsx` — 65 linhas (2022–2026, por bandeira × forma de pagamento), com 3 colunas: **Taxa Adquirente** (retido real, extrato Rede), **Taxa Contratada** (o que o sistema mostrou), **Taxa encontrada no extrato de vendas** (verificação manual do funcionário).
- `contestacoes/Conferência de taxas utilizadas na Conciliação - Meu Prata Loja 04.docx` — texto explicando a metodologia e 2 exemplos de divergência, com prints.

---

## 2. Caso 1 (docx) — Elo Débito à Vista 2022

Funcionário reportou: sistema mostrou 0,94%, extrato real (adquirente) é 0,99%, cálculo manual da "menor taxa efetiva" deu 0,84%.

**Verificação:** rodando o cálculo com granularidade **anual**, o sistema dá 0,84% — bate exatamente com o funcionário. O "0,94%" veio de um cálculo rodado em granularidade **mensal**: nessa modalidade o sistema acha a menor taxa **de cada mês separadamente**, e a média dessas 12 taxas mensais (0,84% em janeiro até 0,99% em meses de baixo volume) dá 0,944% ≈ 0,94%.

**Conclusão:** não é bug — é diferença de metodologia (mensal agrega 12 mínimos locais; anual acha o mínimo único do ano). **Decisão do cliente: granularidade correta para este cliente é sempre ANUAL.**

---

## 3. Caso 2 (docx) — American Express Crédito à Vista 2025

Funcionário reportou: taxa cadastrada 1,98%, sistema usou 1,97% no cálculo.

**Verificação:** nos cálculos anteriores a 21/07, o sistema realmente não casava com a taxa cadastrada e caía no fallback (1,97%). A taxa cadastrada foi editada em 21/07/2026 19:53. Rodando o cálculo com o cadastro atual, o sistema já casa corretamente e usa 1,98%.

**Decisão do cliente: considerar esse caso resolvido** (sem investigar a fundo por que o match falhava antes da edição de 21/07).

---

## 4. Varredura completa — 65 linhas

Cruzei as 65 linhas da planilha do funcionário com o cálculo anual mais recente do processamento `84985160_0002 - 16/07/2026 15:04:03`.

- **2025–2026 (24 linhas):** todas com taxa cadastrada (`calc_origem='cad'`), taxa de contrato ≈ taxa de adquirente — **sem divergência**.
- **2022–2024 (40 linhas):** sem taxa cadastrada (`calc_origem='log'`, fallback). **35 de 40 batem** com a checagem manual do funcionário (diferença ≤ 0,05pp). **5 divergem** — todas em **CREDITO PARCELADO LOJA** (Amex 2023, Mastercard 2023/2024, Visa 2023/2024), diferença de 0,09 a 0,41pp.

Tabela completa das 65 linhas (Ano | Bandeira | Forma | Adquirente(func.) | Contratada(sistema, versão que o funcionário viu) | Extrato manual(func.) | Contrato calculado hoje | Adquirente calculado hoje | Origem | Status):

| Ano | Bandeira | Forma | Adquirente (func.) | Contratada (func. viu) | Extrato manual (func.) | Contrato (hoje) | Adquirente (hoje) | Origem | Status |
|---|---|---|---:|---:|---:|---:|---:|---|---|
| 2022 | American Express | CREDITO A VISTA | 2,54% | 2,54% | 2,54% | 2,5386% | 2,5483% | log | OK |
| 2022 | American Express | CREDITO PARCELADO LOJA | 2,60% | 2,60% | 2,60% | 2,6035% | 2,6035% | log | OK |
| 2022 | Elo | CREDITO A VISTA | 1,99% | 1,98% | 1,97% | 1,9729% | 1,9901% | log | OK |
| 2022 | Elo | CREDITO PARCELADO LOJA | 2,19% | 2,19% | 2,19% | 2,1919% | 2,1919% | log | OK |
| 2022 | Elo | DEBITO A VISTA | 0,99% | 0,94% | 0,84% | 0,8403% | 0,9899% | log | OK (caso do docx) |
| 2022 | Hipercard | CREDITO A VISTA | 1,79% | 1,75% | 1,67% | 1,6687% | 1,7897% | log | OK |
| 2022 | Hipercard | CREDITO PARCELADO LOJA | 2,19% | 2,19% | 2,19% | 2,1905% | 2,1905% | log | OK |
| 2022 | Mastercard | CREDITO A VISTA | 1,69% | 1,35% | 1,25% | 1,2499% | 1,6899% | log | OK |
| 2022 | Mastercard | CREDITO PARCELADO LOJA | 2,09% | 2,08% | 2,08% | 2,0801% | 2,0901% | log | OK |
| 2022 | Mastercard | DEBITO A VISTA | 0,79% | 0,03% | 0,53% | 0,5299% | 0,7901% | log | OK |
| 2022 | Visa | CREDITO A VISTA | 1,59% | 1,57% | 1,54% | 1,5399% | 1,5907% | log | OK |
| 2022 | Visa | CREDITO PARCELADO LOJA | 2,09% | 2,09% | 2,08% | 2,0801% | 2,0899% | log | OK |
| 2022 | Visa | DEBITO A VISTA | 0,79% | 0,75% | 0,70% | 0,6993% | 0,7899% | log | OK |
| 2023 | American Express | CREDITO A VISTA | 2,01% | 1,97% | 1,89% | 1,8900% | 2,0168% | log | OK |
| 2023 | **American Express** | **CREDITO PARCELADO LOJA** | 2,11% | 2,09% | **2,10%** | **2,0100%** | 2,1089% | log | **DIVERGE (-0,09pp)** |
| 2023 | Elo | CREDITO A VISTA | 1,81% | 1,79% | 1,63% | 1,6286% | 1,8406% | log | OK |
| 2023 | Elo | CREDITO PARCELADO LOJA | 2,21% | 2,21% | 2,19% | 2,1897% | 2,2175% | log | OK |
| 2023 | Elo | DEBITO A VISTA | 0,92% | 0,87% | 0,69% | 0,6899% | 0,9115% | log | OK |
| 2023 | Hipercard | CREDITO A VISTA | 1,69% | 1,64% | 1,50% | 1,4998% | 1,6812% | log | OK |
| 2023 | Hipercard | CREDITO PARCELADO LOJA | 2,16% | 2,16% | 2,01% | 2,0101% | 2,1673% | log | OK |
| 2023 | Mastercard | CREDITO A VISTA | 1,60% | 1,07% | 1,12% | 1,1200% | 1,6004% | log | OK |
| 2023 | **Mastercard** | **CREDITO PARCELADO LOJA** | 2,01% | 1,92% | **2,00%** | **1,5901%** | 2,0102% | log | **DIVERGE (-0,41pp)** |
| 2023 | Mastercard | DEBITO A VISTA | 0,65% | 0,00% | 0,44% | 0,4402% | 0,6506% | log | OK |
| 2023 | Visa | CREDITO A VISTA | 1,60% | 1,31% | 1,09% | 1,0899% | 1,6000% | log | OK |
| 2023 | **Visa** | **CREDITO PARCELADO LOJA** | 2,01% | 1,79% | **2,00%** | **1,6000%** | 2,0094% | log | **DIVERGE (-0,40pp)** |
| 2023 | Visa | DEBITO A VISTA | 0,65% | 0,15% | 0,44% | 0,4401% | 0,6508% | log | OK |
| 2024 | American Express | CREDITO A VISTA | 2,01% | 1,93% | 1,83% | 1,8297% | 2,0096% | log | OK |
| 2024 | American Express | CREDITO PARCELADO LOJA | 2,11% | 2,11% | 2,11% | 2,1102% | 2,1102% | log | OK |
| 2024 | Diners | CREDITO A VISTA | 1,59% | 1,59% | 1,59% | 1,5896% | 1,5896% | log | OK |
| 2024 | Elo | CREDITO A VISTA | 1,65% | 1,63% | 1,61% | 1,6088% | 1,6402% | log | OK |
| 2024 | Elo | CREDITO PARCELADO LOJA | 2,26% | 2,26% | 2,24% | 2,2385% | 2,2608% | log | OK |
| 2024 | Elo | DEBITO A VISTA | 0,81% | 0,76% | 0,67% | 0,6686% | 0,8086% | log | OK |
| 2024 | Hipercard | CREDITO A VISTA | 1,60% | 1,58% | 1,56% | 1,5628% | 1,5992% | log | OK |
| 2024 | Hipercard | CREDITO PARCELADO LOJA | 2,01% | 2,01% | 2,01% | 2,0085% | 2,0085% | log | OK |
| 2024 | Mastercard | CREDITO A VISTA | 1,60% | 1,07% | 1,09% | 1,0901% | 1,5980% | log | OK |
| 2024 | **Mastercard** | **CREDITO PARCELADO LOJA** | 2,01% | 1,73% | **1,97%** | **1,5600%** | 2,0072% | log | **DIVERGE (-0,41pp)** |
| 2024 | Mastercard | DEBITO A VISTA | 0,65% | 0,00% | 0,42% | 0,4201% | 0,6475% | log | OK |
| 2024 | Visa | CREDITO A VISTA | 1,60% | 1,23% | 1,08% | 1,0801% | 1,6001% | log | OK |
| 2024 | **Visa** | **CREDITO PARCELADO LOJA** | 2,01% | 1,68% | **1,98%** | **1,5801%** | 2,0090% | log | **DIVERGE (-0,40pp)** |
| 2024 | Visa | DEBITO A VISTA | 0,65% | 0,07% | 0,43% | 0,4300% | 0,6500% | log | OK |
| 2025 | American Express | CREDITO A VISTA | 1,98% | 1,97% | 1,98% | 1,9809% | 1,9809% | cad | OK |
| 2025 | Diners | CREDITO A VISTA | 1,61% | 1,61% | 1,61% | 1,6107% | 1,6107% | cad | OK |
| 2025 | Elo | CREDITO A VISTA | 1,61% | 1,61% | 1,61% | 1,6100% | 1,6100% | cad | OK |
| 2025 | Elo | CREDITO PARCELADO LOJA | 2,24% | 2,24% | 2,24% | 2,2390% | 2,2390% | cad | OK |
| 2025 | Elo | DEBITO A VISTA | 0,79% | 0,78% | 0,78% | 0,7824% | 0,7824% | cad | OK |
| 2025 | Hipercard | CREDITO A VISTA | 1,57% | 1,61% | 1,61% | 1,6119% | 1,5711% | cad | OK |
| 2025 | Mastercard | CREDITO A VISTA | 1,56% | 1,56% | 1,56% | 1,5600% | 1,5600% | cad | OK |
| 2025 | Mastercard | CREDITO PARCELADO LOJA | 1,98% | 1,98% | 1,98% | 1,9800% | 1,9794% | cad | OK |
| 2025 | Mastercard | DEBITO A VISTA | 0,61% | 0,61% | 0,61% | 0,6100% | 0,6100% | cad | OK |
| 2025 | Visa | CREDITO A VISTA | 1,54% | 1,56% | 1,56% | 1,5604% | 1,5604% | cad | OK |
| 2025 | Visa | CREDITO PARCELADO LOJA | 1,98% | 1,98% | 1,98% | 1,9807% | 1,9807% | cad | OK |
| 2025 | Visa | DEBITO A VISTA | 0,61% | 0,61% | 0,61% | 0,6102% | 0,6102% | cad | OK |
| 2026 | American Express | CREDITO A VISTA | 1,98% | 1,97% | 1,98% | 1,9795% | 1,9795% | cad | OK |
| 2026 | Cabal | DEBITO A VISTA | 0,78% | 0,78% | 0,78% | 0,7798% | 0,7798% | cad | OK |
| 2026 | Diners | CREDITO A VISTA | 1,63% | 1,61% | 1,61% | 1,6251% | 1,6251% | cad | OK |
| 2026 | Elo | CREDITO A VISTA | 1,60% | 1,61% | 1,61% | 1,6097% | 1,6097% | cad | OK |
| 2026 | Elo | CREDITO PARCELADO LOJA | 2,24% | 2,24% | 2,24% | 2,2407% | 2,2407% | cad | OK |
| 2026 | Elo | DEBITO A VISTA | 0,79% | 0,78% | 0,78% | 0,7816% | 0,7816% | cad | OK |
| 2026 | Mastercard | CREDITO A VISTA | 1,56% | 1,56% | 1,56% | 1,5600% | 1,5600% | cad | OK |
| 2026 | Mastercard | CREDITO PARCELADO LOJA | 1,98% | 1,98% | 1,98% | 1,9800% | 1,9800% | cad | OK |
| 2026 | Mastercard | DEBITO A VISTA | 0,61% | 0,61% | 0,61% | 0,6100% | 0,6100% | cad | OK |
| 2026 | Visa | CREDITO A VISTA | 1,56% | 1,56% | 1,56% | 1,5600% | 1,5600% | cad | OK |
| 2026 | Visa | CREDITO PARCELADO LOJA | 1,98% | 1,98% | 1,98% | 1,9802% | 1,9802% | cad | OK |
| 2026 | Visa | DEBITO A VISTA | 0,61% | 0,61% | 0,61% | 0,6099% | 0,6099% | cad | OK |

---

## 5. As 5 divergências — causa e decisão

Todas em **CREDITO PARCELADO LOJA**. Dentro dessa categoria existem taxas diferentes por número de parcelas — ex., Mastercard:

| Ano | Parcelas | Taxa mínima | Taxa máxima | Qtd. vendas |
|---|---|---|---|---|
| 2023 | 2 | 2,00% | 2,10% | 1.365 |
| 2023 | 3 | 1,59% | 2,09% | 1.691 |
| 2024 | 2 | 1,56% | 2,02% | 2.987 |
| 2024 | 3 | 1,56% | 2,02% | 4.363 |

O fallback "menor taxa do período" agrupa só por bandeira + forma de pagamento, **sem considerar número de parcelas** — pega a taxa mais barata de qualquer parcelamento (ex.: 3x) e aplica pra toda a categoria "Parcelado Loja", inclusive vendas em 2x com taxa contratual mais alta. O próprio cadastro de taxas contratadas também trata "Parcelado Loja" como faixa única (sem diferenciar por parcela), então esse comportamento é consistente com o resto do sistema.

**Decisão do cliente (22/07/2026): não segregar por número de parcelas.** As 5 divergências são esperadas dado esse critério e **não são bug** — fechadas sem alteração de código.

---

## 6. Resumo

| # | Item | Status |
|---|---|---|
| 1 | Caso Elo Débito à Vista 2022 (docx) | ✅ Esclarecido — diferença mensal vs anual, não é bug |
| 2 | Caso Amex Crédito à Vista 2025 (docx) | ✅ Considerado resolvido por decisão do cliente |
| 3 | Granularidade a usar para este cliente | ✅ Definida: sempre ANUAL |
| 4 | Varredura completa 65 linhas | ✅ Concluída — 60 OK, 5 divergências explicadas |
| 5 | Divergências em "Parcelado Loja" | ✅ Fechado — decisão: não segregar por parcela, comportamento esperado |

## 7. Arquivos relevantes

- `contestacoes/Conferência taxas - - Meu Prata Loja 04.xlsx` — planilha de conferência do funcionário (65 linhas)
- `contestacoes/Conferência de taxas utilizadas na Conciliação - Meu Prata Loja 04.docx` — relato/metodologia do funcionário
- `contestacoes/comparativo_pos_fix.tsv` — extração bruta do cálculo usada na varredura
