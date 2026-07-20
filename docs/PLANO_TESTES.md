# Plano de Testes e Homologação - Concilie v1.8

Este documento serve como roteiro para validação da qualidade (QA) do sistema antes da entrega ao cliente.

---

## 🏗️ 1. Testes de Instalação e Ambiente

| ID | Cenário | Passos | Resultado Esperado | Status |
|----|---------|--------|--------------------|--------|
| T1-01 | Distribuição Limpa | 1. Baixar o pacote `.zip` ou pasta distribuída.<br>2. Extrair em um diretório limpo (ex: `C:\TesteConcilie`). | Extração ocorre sem erros. Estrutura de pastas (`_internal`, `FinancialChecker.exe`) está correta. | [ ] |
| T1-02 | Execução Standalone | 1. Executar `FinancialChecker.exe`. | Janela de terminal abre. Navegador abre em `localhost:3000`. Sem erros de importação Python. | [ ] |
| T1-03 | Persistência do Banco | 1. Criar um registro qualquer (ex: De-Para).<br>2. Fechar o sistema.<br>3. Reabrir. | O registro criado deve continuar existindo. | [ ] |

## 🚀 2. Testes de Importação (Core)

| ID | Cenário | Passos | Resultado Esperado | Status |
|----|---------|--------|--------------------|--------|
| T2-01 | Detecção de Arquivo (Rede) | 1. Ir em "Importar > De-Para".<br>2. Clicar em "+ Nova Regra".<br>3. Selecionar arquivo Multi-Sheet da Rede.<br>4. Clicar em "Ler". | Sistema deve identificar corretamente a aba de dados e listar as colunas no dropdown. | [ ] |
| T2-02 | Importação de Vendas | 1. Ir em "Importar > Vendas".<br>2. Subir arquivo de vendas padrão.<br>3. Acompanhar barra de progresso. | Arquivo processado 100%. Mensagem de sucesso. Dados aparecem no dashboard. | [ ] |
| T2-03 | Arquivo Inválido | 1. Tentar importar um PDF ou imagem na tela de importação. | Sistema deve rejeitar o arquivo com mensagem de erro amigável. | [ ] |

## ⚙️ 3. Testes Funcionais

| ID | Cenário | Passos | Resultado Esperado | Status |
|----|---------|--------|--------------------|--------|
| T3-01 | De-Para Manual | 1. Criar regra De-Para: Coluna Arquivo "Data Venda" -> Sistema "dt_venda".<br>2. Importar arquivo usando essa regra. | Dados importados devem respeitar o mapeamento. Data deve estar correta no banco. | [ ] |
| T3-02 | Cálculo de Taxas | 1. Importar Vendas.<br>2. Rodar rotina "Calcular Taxas". | Coluna de "Valor Líquido Calculado" deve ser preenchida baseada na taxa cadastrada. | [ ] |
| T3-03 | Relatório Sintético | 1. Ir em "Relatórios".<br>2. Gerar relatório de vendas por período. | Tabela deve carregar com dados coerentes. Exportação para Excel deve funcionar. | [ ] |

## 🖥️ 4. Testes de Interface (UI)

| ID | Cenário | Passos | Resultado Esperado | Status |
|----|---------|--------|--------------------|--------|
| T4-01 | Responsividade | 1. Redimensionar janela do navegador. | Menu lateral e tabelas devem se ajustar sem quebrar o layout. | [ ] |
| T4-02 | Navegação | 1. Clicar em todos os itens do menu lateral. | Todas as páginas devem carregar (404 não permitido). | [ ] |
| T4-03 | Feedback Visual | 1. Executar ação demorada (Importação). | Deve aparecer spinner/loading indicando processamento. | [ ] |

---

**Responsável pelos Testes:** __________________________
**Data da Homologação:** ___/___/______
