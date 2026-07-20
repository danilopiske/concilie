# Descritivo Funcional do Sistema Concilie

Este documento detalha os módulos funcionais, recursos e capacidades do sistema **Concilie - Financial Checker**. O sistema foi desenhado para atender às necessidades complexas de conciliação de cartões, auditoria de taxas e gestão financeira de varejistas.

---

## 1. Módulo de Importação Inteligente

O coração do sistema reside na sua capacidade de ingerir dados de diversas fontes com inteligência e flexibilidade.

*   **Multiformato**: Suporte nativo para arquivos `.csv`, `.xls`, `.xlsx`, `.txt` e Extratos Bancários (`.ofx`).
*   **Detecção Automática (Smart Header Detection)**:
    *   O sistema identifica automaticamente o tipo de arquivo (Venda, Recebimento, Bancário) baseado no conteúdo e cabeçalhos.
    *   Para arquivos complexos (ex: Relatórios da Rede), o sistema ignora capas, abas de resumo e identifica automaticamente a aba correta contendo os dados transacionais.
*   **De-Para Dinâmico**:
    *   Interface visual para criação de regras de mapeamento de colunas.
    *   Permite importar layouts desconhecidos mapeando colunas do arquivo para colunas do sistema (ex: "Data Venda" -> "dt_venda").
*   **Processamento Assíncrono**:
    *   Uploads grandes são processados em background, liberando o usuário para continuar operando o sistema.
    *   Barra de progresso em tempo real e log de validação linha a linha.

## 2. Conciliação Automática

O motor de conciliação cruza informações de vendas registradas no ERP/POS com os dados fornecidos pelas adquirentes (Cielo, Rede, Getnet, etc.).

*   **Conciliação Vendas x Cartões**: Verifica se todas as vendas passadas no caixa foram efetivamente capturadas pela adquirente.
*   **Conciliação Bancária**: Cruza os recebimentos previstos (Adquirente) com o que efetivamente caiu na conta bancária (Extrato OFX).
*   **Auditoria de Taxas**:
    *   Recálculo automático de taxas administrativas por bandeira e modalidade (Débito/Crédito).
    *   Alerta de divergências entre a taxa contratada e a taxa cobrada.

## 3. Gestão de Transações (Financial Checker)

Interface analítica para exploração dos dados financeiros.

*   **Painel do Analista**: Visão macro e micro das transações.
*   **Correção de Dados**: Ferramentas para ajustes manuais auditados em transações com problemas (ex: NSU divergente, Data incorreta).
*   **Filtros Avançados**: Busca por NSU, Autorização, Valor, Data, Bandeira, Adquirente.

## 4. Dashboards e Relatórios

Visualização de dados para tomada de decisão estratégica.

*   **Dashboard Executivo**: KPIs principais (Total Vendido, Taxa Média, Total Recebido).
*   **Relatórios Exportáveis**: Todos os grids e visões podem ser exportados para Excel ou PDF para auditorias externas.
*   **Visão por Filial**: Suporte multi-loja, permitindo segregar ou consolidar a visão financeira de grupos econômicos.

## 5. Arquitetura e Segurança

*   **Banco de Dados Local ou Servidor**: Flexibilidade para rodar com SQLite (arquivo único, zero config) ou MySQL (alta performance, multiusuário).
*   **Interface Web Moderna**: Acesso via navegador, responsivo e rápido.
*   **Executável Único (Standalone)**: O sistema pode ser distribuído como um único arquivo `.exe`, sem necessidade de instalação complexa de servidores web ou bancos de dados na máquina do cliente.

---

**Concilie - Soluções em Conciliação Financeira**
