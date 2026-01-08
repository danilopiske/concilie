# Financial Checker v2.0 — Descrição Detalhada

## 1. Visão Geral

O **Financial Checker v2.0** é um sistema de conciliação financeira profissional, multiplataforma, com suporte híbrido a bancos **MySQL** (produção, multiusuário) e **SQLite** (cliente, single user). Foca em importação, análise, gestão e cálculo automático de grandes volumes de transações financeiras, principalmente oriundas de adquirentes, gateways, bancos e operações de cartões.

**Destaques:**
- **Híbrido MySQL/SQLite** (distribuição e nuvem)
- Totalmente modular (UI Panel+Python, processamento, banco)
- Importação de planilhas e arquivos financeiros diversos (.csv, .xls, .xlsx)
- Análise, agregação e cálculos automáticos por período, bandeira, forma de pagamento, recebedores, etc.
- Geração de relatórios PDF e dashboards interativos (Plotly)

---

## 2. Arquitetura e Componentes Principais

### 2.1 Arquitetura de Pastas Essenciais
- `main.py`: Ponto de entrada da aplicação (Panel/Serve)
- `modules/`: Módulos de interface (UI para importação, gestão, cálculos, analista, gráficos)
- `proc/`: Processamento de dados (importação, usuários, integrações)
- `conf/`: Configurações globais, conexões, utilitários e helpers para banco de dados
- `data/`: Banco SQLite local e dados
- `relatorios/`: Templates de relatórios
- `dev_tools/`: Scripts para migração, análise, manutenção

### 2.2 Fluxo de Uso Geral
- Instalação (script automático ou manual, suporte a Windows/Linux)
- Configuração automática do banco (MySQL ou SQLite)
- Interface web via Panel acessível localmente (http://localhost:8500)
- Login com sistema de autenticação local
- Módulos de importação para dados financeiros
- Processamentos consolidados em banco
- Visualização de gráficos/dashboards e geração de relatórios

---

## 3. Funcionalidades Detalhadas

### 3.1 Interface e Módulos UI
- **Importação (ui_importacao.py):**    
  - Importa arquivos (xls, xlsx, csv)  
  - Normaliza e classifica transações, converte colunas (de-para), identifica e corrige cabeçalhos
  - Relacionamento com clientes, contextos, e processamento batelada
- **Gestão (ui_gestao.py):**  
  - Cadastro e gestão de clientes (ECs)
  - Controle de bandeiras e formas de pagamento aceitas por cliente
  - Cadastro e cópia de taxas configuradas por EC
  - Termos de uso, permissões, integração com regras de negócio
- **Analista (ui_analista.py):**  
  - Criação, edição e exclusão de análises financeiras  
  - Gerenciamento de arquivos, bandeiras, formas, períodos e recebíveis por análise
  - Agregação de indicadores, relatórios customizáveis por filtros
- **Cálculos (ui_calculos.py):**  
  - Execução de cálculos automáticos de taxas, recebíveis, valores
  - Processos de agregação por semestre, trimestre, ano, bandeira, forma de pagamento
  - Ajustes, atualizações e persistência dos resultados no banco
- **Gráficos e Relatórios (grafico_views.py, reports.py):**  
  - Geração de dashboards interativos Plotly
  - Relatórios em PDF, análises agregadas
  - Visualizações por bandeira, forma de pagamento, período, etc.

### 3.2 Banco de Dados (estrutura exemplo — ver database_structure.txt)
- Tabelas de controle de análises, arquivos, bandeiras, formas de pagamento, períodos, usuários, clientes, taxas, etc.
- Suporte a migração de MySQL para SQLite para distribuição rápida
- Processamento de dados massivos com agregação eficiente (via SQLAlchemy e Pandas)

### 3.3 Configuração e Operação
- **Instalação** via scripts automáticos ou manual, dependências no `requirements.txt` e gerenciamento via Poetry
- **Configuração automática** com seleção interativa do tipo de banco (`configure_db.py`, `.db_config`, ou variável de ambiente)
- **Autenticação** local baseada em hash de senha SHA-256, armazenamento de usuários em JSON
- **Processamento paralelo** otimizado e preparado para grandes volumes

### 3.4 Scripts e Ferramentas
- Migração automática MySQL→SQLite (`dev_tools/migrate_mysql_to_sqlite.py`)
- Limpeza e preparação de distribuição
- Criação de novos bancos a partir de templates

---

## 4. Fluxo de Trabalho Comum

1. **Instalação**  
   - Usuário final: `INSTALAR_COMPLETO.bat` ou `Instalar.bat`
   - Desenvolvedor: Clone git + ambiente virtual + requirements/poetry
2. **Configurar Banco:**  
   - Definição MySQL/SQLite
3. **Iniciar sistema:**  
   - Interface web Panel local
4. **Login/administração:**  
   - login padrão: admin/1234 (recomenda-se trocar na primeira execução)
5. **Importação/processamento de dados**
6. **Visualização e geração de relatórios**

---

## 5. Pontos Fortes e Atenções para Migração

### Pontos Fortes
- Modularidade clara
- Facilidade para adaptar camadas (UI, DB, processamento)
- Portabilidade/capacidade de rodar standalone (SQLite) ou cloud/server (MySQL)
- Sistema de autenticação embutido

### Atenção para Migração
- Existência de código SQL duplicado (precisa de refatoração para evitar bugs em migração)
- Processamento fortemente acoplado ao SQLAlchemy (atenção ao migrar DB handler)
- Documentação atualmente fragmentada, consolidar um único guia robusto (como este .md)
- Falta de testes automatizados (construir suíte se migrar para outra stack)

---

## 6. Tecnologias Empregadas

- **Python 3.11**
- **Panel** (Holoviz)
- **SQLAlchemy**
- **Pandas**
- **Plotly**
- **Poetry**

---

## 7. Estrutura Resumida de Diretórios

```plaintext
Financial_P/
├── main.py                      # Entry point Panel
├── configure_db.py              # Setup automático banco
├── requirements.txt/pyproject.toml  # Dependências
├── conf/                        # Configurações e helpers
├── modules/                     # UI modular
├── proc/                        # Processamento
├── data/                        # SQLite, dados, exemplos
├── relatorios/                  # Templates relatórios
├── dev_tools/                   # Scripts utilitários/migração
```
---

## 8. Checklist Básico Pós-Instalação

- [ ] Sistema instalado/testado com `TESTE_INSTALACAO.bat`
- [ ] Login inicial, criação e troca de senha
- [ ] Importação de dados e processamento
- [ ] Visualização de dashboards/relatórios
- [ ] Backup de banco/dados configurado

---

Se deseja, ajuste a redação, expanda exemplos de fluxos ou detalhe ainda mais a lógica Python de algum módulo. Basta pedir!

