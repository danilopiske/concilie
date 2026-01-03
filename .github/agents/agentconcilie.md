## Proteção contra Código Duplicado e Erros de Indentação

### ✅ SEMPRE FAZER
- Antes de salvar ou commitar funções novas ou alteradas:
  - Revisar se não há blocos duplicados (código colado acidentalmente, prints ou dicionários soltos).
  - Garantir que cada função tenha apenas o corpo esperado, sem trechos de outras funções.
  - Conferir a indentação de todos os blocos (especialmente após colagens múltiplas).
  - Usar ferramentas de lint/format (ex: black, flake8) para detectar indentação e duplicidade.
  - Se for editar via IA, revisar o diff para garantir que não há inserção de código fora do contexto correto.

### ❌ NUNCA FAZER
- Nunca colar código de outra função dentro de uma função já existente.
- Nunca deixar prints, dicionários ou laços soltos fora do corpo de funções.
- Nunca salvar arquivos com erros de indentação (IndentationError) ou blocos duplicados.

### Resolução Rápida de Problemas
| Problema | Causa | Solução |
|----------|-------|---------|
| IndentationError | Código colado fora do bloco, duplicidade, mistura de funções | Revisar função, remover blocos estranhos, rodar linter |
| Código duplicado | Colagem acidental, edição IA sem revisão | Conferir diff, remover duplicatas antes de salvar |

# AGENT.MD — FinChecker Copilot Knowledge

## ✨ Missão
Este agente deve sugerir código **sempre aderente** às seguintes regras técnicas, de arquitetura e estilo. Use este arquivo (`agent.md`) como prompt/contexto ao configurar GitHub Copilot, Codespaces, Cursor AI ou assistente de IA similar.

---

## 🔸 Stack & Frameworks
- **Python 3.8+**
- **Panel (HoloViz)** para UI
- **SQLAlchemy** para banco de dados (MySQL e SQLite)
- **Pandas** para ETL/processamento
- **Plotly** para gráficos
- **PDFKit** + wkhtmltopdf para PDF

## 🔸 Banco de Dados - CONTEXTO CRÍTICO

### 🎯 **PREMISSA FUNDAMENTAL: COMPATIBILIDADE DUPLA**
**SEMPRE** desenvolver código compatível com **MySQL E SQLite** simultaneamente:
- Sistema roda com **MySQL** em produção (servidor)
- Sistema roda com **SQLite** em distribuição standalone (sem servidor)
- **NUNCA** usar sintaxe exclusiva de um banco sem abstração
- **SEMPRE** usar funções helper do `sql_adapter.py` para SQL específico
- **SEMPRE** testar alterações em ambos os bancos quando possível

### 📋 Diferenças Críticas MySQL vs SQLite
| Recurso | MySQL | SQLite | Solução |
|---------|-------|--------|---------|
| `INSERT IGNORE` | ✅ | ❌ | Usar `INSERT OR IGNORE` (SQLite) - função `_adapt_sql()` converte automaticamente |
| `NOW()` | ✅ | ❌ | Usar `_current_timestamp_sql(engine)` → retorna `CURRENT_TIMESTAMP` |
| `DATE_FORMAT()` | ✅ | ❌ | Usar `_date_format_sql(engine, col, fmt)` |
| `CONCAT()` | ✅ | ❌ | Usar `_concat_sql(engine, *args)` |
| Comparação case-insensitive | `COLLATE` | `COLLATE NOCASE` ou `UPPER()` | Usar `UPPER(col1) = UPPER(col2)` |
| UPSERT | `ON DUPLICATE KEY UPDATE` | `ON CONFLICT ... DO UPDATE` | Usar `_upsert_sql(engine, ...)` |

### 🛠️ Boas Práticas de Compatibilidade
1. **Sempre incluir `engine` como primeiro parâmetro** em funções SQL adapter
2. **Verificar strings vazias vs NULL**: `if value is not None` (não `if value`)
3. **Usar `_adapt_sql(engine, sql)`** em `exec_sql()`, `fetch_one()` e `fetch_all()`
4. **Tipos de dados**: 
   - Monetários: **DECIMAL(18,2)** nunca DOUBLE/FLOAT
   - **PROBLEMA COMUM**: DOUBLE causa imprecisão (0.30 → 0.3097)
   - **SOLUÇÃO**: Sempre usar DECIMAL para valores monetários e percentuais

### 📚 Funções SQL Adapter Disponíveis (conf/funcoesbd.py)

**SEMPRE usar estas funções em vez de SQL direto específico de banco:**

```python
# Comparação case-insensitive (texto)
_normalize_text_compare(engine, column, param)
# MySQL: UPPER(column) = UPPER(:param)
# SQLite: UPPER(column) = UPPER(:param)

# Formatação de data
_date_format_sql(engine, column, format_str)
# MySQL: DATE_FORMAT(column, format_str)
# SQLite: strftime(format_convertido, column)

# Concatenação
_concat_sql(engine, *args)
# MySQL: CONCAT(arg1, arg2, ...)
# SQLite: arg1 || arg2 || ...

# Insert ignore
_insert_ignore_sql(engine, table, columns, values)
# MySQL: INSERT IGNORE INTO...
# SQLite: INSERT OR IGNORE INTO...

# Timestamp atual
_current_timestamp_sql(engine)
# MySQL/SQLite: CURRENT_TIMESTAMP

# UPSERT (insert or update)
_upsert_sql(engine, table, columns, update_columns)
# MySQL: INSERT ... ON DUPLICATE KEY UPDATE
# SQLite: INSERT ... ON CONFLICT DO UPDATE

# Extrair ano/mês/trimestre/semestre
_year_sql(engine, column)
_month_sql(engine, column)
_quarter_sql(engine, column)
_semester_sql(engine, column)

# Obter colunas de tabela
_get_table_columns(engine, table_name)

# Adaptar SQL automaticamente (INSERT IGNORE → INSERT OR IGNORE)
_adapt_sql(engine, sql)
```

**Exemplo de uso correto:**
```python
# ❌ ERRADO - SQL específico do MySQL
sql = "INSERT IGNORE INTO tabela (a, b) VALUES (:a, :b)"

# ✅ CORRETO - Usando helper
sql = _insert_ignore_sql(engine, "tabela", "a, b", ":a, :b")

# ❌ ERRADO - NOW() só funciona no MySQL
sql = "UPDATE tabela SET updated = NOW()"

# ✅ CORRETO - Compatível com ambos
sql = f"UPDATE tabela SET updated = {_current_timestamp_sql(engine)}"

# ❌ ERRADO - Comparação case-sensitive
sql = "WHERE contexto = :ctx"

# ✅ CORRETO - Case-insensitive
sql = f"WHERE {_normalize_text_compare(engine, 'contexto', 'ctx')}"
```

---

## 🔸 Estrutura de Tabelas do Banco MySQL

### 📊 Tabelas Principais - Vendas
**vendas_processadas** (principal) | **vendas_filtradas** (rejeitadas) | **vendas_diversas** (casos especiais)
- `id` INT AUTO_INCREMENT PK
- `Data_da_venda` DATETIME
- `Adquirente` VARCHAR(45)
- `Bandeira` TEXT (⚠️ deveria ser VARCHAR)
- `Forma_de_pagamento` TEXT (⚠️ deveria ser VARCHAR)
- `Quantidade_de_parcelas` BIGINT
- `Valor_da_venda` **DOUBLE** ⚠️ **PROBLEMA: deveria ser DECIMAL(18,2)**
- `Taxas_Perc` **DOUBLE** ⚠️ **PROBLEMA: deveria ser DECIMAL(18,2)**
- `Valor_descontado` **DOUBLE** ⚠️ **PROBLEMA: deveria ser DECIMAL(18,2)**
- `Taxas_RR` **DOUBLE** ⚠️ **PROBLEMA: deveria ser DECIMAL(18,2)**
- `Valor_RR` **DOUBLE** ⚠️ **PROBLEMA: deveria ser DECIMAL(18,2)**
- `Valor_líquido_da_venda` **DOUBLE** ⚠️ **PROBLEMA: deveria ser DECIMAL(18,2)**
- `processamentoid` TEXT
- `cliente_id` BIGINT
- `ec_id` BIGINT

**vendas_filtradas** (estrutura otimizada):
- Mesmas colunas mas com tipos corretos: DECIMAL(12,2) para valores monetários ✅
- DATE em vez de DATETIME para datas

### 📊 Tabelas Principais - Recebíveis
**recebiveis_processados** | **recebiveis_filtrados**
- `id` INT AUTO_INCREMENT PK
- `recebivel_id` VARCHAR(45)
- `data_pagamento` DATETIME
- `data_recebivel` DATETIME
- `lancamento` TEXT
- `valor_recebivel` **DOUBLE** ⚠️ **PROBLEMA: deveria ser DECIMAL(18,2)**
- `valor_liquido` **DOUBLE** ⚠️ **PROBLEMA: deveria ser DECIMAL(18,2)**
- `adquirente` VARCHAR(50)
- `processamentoid` TEXT
- `cliente_id` BIGINT
- `ec_id` BIGINT

### 📊 Tabela de Cálculos
**vendas_calculos** (armazena cálculos e comparações)
- `id` INT AUTO_INCREMENT PK
- `id_venda` INT (FK para vendas)
- `calc_id` VARCHAR(50) (identificador do processamento de cálculo)
- `bandeira` VARCHAR(50)
- `forma_pagamento` VARCHAR(50)
- `vl_venda` DECIMAL(15,2) ✅
- `tx_venda` DECIMAL(10,4) ✅ (taxa original do arquivo)
- `desc_venda` DECIMAL(15,2) ✅
- `tx_calc` DECIMAL(10,4) ✅ (taxa calculada/cadastrada)
- `desc_calc` DECIMAL(15,2) ✅
- `perda` DECIMAL(15,2) ✅ (diferença entre valores)
- `tx_rr_calc` DECIMAL(15,2) ✅
- `vl_rr_calc` DECIMAL(15,2) ✅
- `perda_rr` DECIMAL(15,2) ✅

### 📊 Gestão de Taxas
**taxas** (cadastro de taxas por EC)
- `id` INT AUTO_INCREMENT PK
- `ec` VARCHAR(20) - estabelecimento comercial
- `bandeira` VARCHAR(50) NULL - **NULL = taxa genérica (todas as bandeiras)**
- `forma_pagamento` VARCHAR(50)
- `parcelado` CHAR(1) - 'S' ou 'N'
- `parcelas_ini` INT
- `parcelas_fim` INT
- `data_ini` DATE
- `data_fim` DATE
- `taxa` DECIMAL(10,2) ✅
- `contexto` VARCHAR(50) - permite múltiplos cenários

### 📊 Gestão de Clientes/ECs
**clientes**
- `cliente_id` INT PK
- `nome_fantasia` VARCHAR(255)
- `razao_social` VARCHAR(255)
- `cnpj` VARCHAR(20)

**ecs** (estabelecimentos comerciais)
- `id` INT AUTO_INCREMENT PK
- `ec_id` VARCHAR(20) UNIQUE
- `descricao` VARCHAR(255)

**ecs_cliente** (relacionamento N:N)
- `cliente_id` INT PK
- `ec_id` VARCHAR(100) PK

**enderecos**, **contatos**, **dados_bancarios** (relacionados a clientes)

### 📊 De-Para e Configurações
**depara_colunas** (mapeamento de colunas)
- `id` INT AUTO_INCREMENT PK
- `origem_nome` VARCHAR(255) - nome da coluna no arquivo
- `destino_nome` VARCHAR(255) - nome da coluna no sistema
- `contexto` VARCHAR(50)
- `tipo_origem` CHAR(1) - 'V' (vendas), 'L' (lançamentos), 'R' (recebíveis)
- `tipo_preenchimento` VARCHAR(20) - 'fixo', 'coluna', etc
- `valor_padrao` VARCHAR(255)
- `ativo` TINYINT(1)

**depara_controle** (colunas disponíveis)
- `nome_coluna` VARCHAR(100)
- `mapeavel` ENUM('mapeavel','nao_mapeavel')

**bandeiras_disponiveis** | **bandeiras_cliente**
- Gestão de bandeiras aceitas por EC

**termos_filtraveis**
- Termos que marcam vendas para filtrar (ex: "cancelada", "erro")

### 📊 Contextos e Usuários
**contextos** (cenários/ambientes diferentes)
- `id` INT AUTO_INCREMENT PK
- `nome` VARCHAR(100) UNIQUE
- `descricao` TEXT
- `ativo` TINYINT(1)

**usuarios**
- `id` INT AUTO_INCREMENT PK
- `usuario` VARCHAR(50) UNIQUE
- `senha` CHAR(64) - hash SHA256
- `nome` VARCHAR(100)
- `empresa` VARCHAR(100)
- `grupo` VARCHAR(50)
- `ativo` TINYINT(1)

### 📊 Controle e Logs
**controle_processamentos**
- `id_processamento` VARCHAR(50) PK (formato: "EC_SEQUENCIA - DATA")
- `cliente_id` VARCHAR(50)
- `ec_id` VARCHAR(50)
- `adquirente` VARCHAR(100)
- `data_processamento` DATETIME

**log_correcoes_importacao**
- Histórico de correções retroativas (bandeiras, formas de pagamento)
- `tipo_correcao` VARCHAR(50)
- `valor_antigo` / `valor_novo` VARCHAR(255)
- `linhas_afetadas` INT
- `usuario` VARCHAR(100)
- `data_correcao` DATETIME

### 📊 Análises (feature adicional)
**analises** + **analises_arquivos** + **analises_bandeiras** + **analises_formas_pagamento** + **analises_periodos** + **analises_tipos_recebiveis**
- Sistema de análise agregada de múltiplos arquivos

### 📊 Views (consultas pré-calculadas)
- `vw_grafico_vendas_por_bandeira`
- `vw_grafico_vendas_por_forma_pagamento`
- `vw_grafico_vendas_por_mes`
- `vw_grafico_valor_medio_por_bandeira`
- `vw_min_max_taxas_semestre`
- `vw_min_taxa_bandeira_forma_ano`
- `vw_perdas_por_semestre`
- `vw_sumario_recebiveis_semestre`
- `vw_contagem_taxas_bandeira_forma_ano`
- `vw_contagem_transacoes_ano_bandeira_modalidade`

### ⚠️ PROBLEMAS IDENTIFICADOS NA ESTRUTURA ATUAL

1. **CRÍTICO - Tipos DOUBLE em vez de DECIMAL:**
   - `vendas_processadas`: Valor_da_venda, Taxas_Perc, Valor_descontado, Taxas_RR, Valor_RR, Valor_líquido
   - `vendas_diversas`: Mesmas colunas
   - `recebiveis_processados/filtrados`: valor_recebivel, valor_liquido
   - **Consequência**: Imprecisão monetária (0.30 vira 0.3097)
   - **Solução**: ALTER TABLE ... MODIFY COLUMN ... DECIMAL(18,2)

2. **TEXT em vez de VARCHAR:**
   - `Bandeira`, `Forma_de_pagamento` como TEXT impede indexação eficiente
   - **Solução**: Alterar para VARCHAR(100) ou VARCHAR(200)

3. **Inconsistência entre tabelas:**
   - `vendas_filtradas` usa DECIMAL(12,2) corretamente ✅
   - `vendas_processadas` usa DOUBLE incorretamente ❌
   - **Solução**: Padronizar DECIMAL(18,2) em todas

### 🔧 Script de Correção (MySQL)
```sql
-- Corrigir vendas_processadas
ALTER TABLE vendas_processadas MODIFY COLUMN Valor_da_venda DECIMAL(18,2);
ALTER TABLE vendas_processadas MODIFY COLUMN Valor_descontado DECIMAL(18,2);
ALTER TABLE vendas_processadas MODIFY COLUMN Valor_RR DECIMAL(18,2);
ALTER TABLE vendas_processadas MODIFY COLUMN Taxas_Perc DECIMAL(18,2);
ALTER TABLE vendas_processadas MODIFY COLUMN Taxas_RR DECIMAL(18,2);
ALTER TABLE vendas_processadas MODIFY COLUMN Valor_líquido_da_venda DECIMAL(18,2);
ALTER TABLE vendas_processadas MODIFY COLUMN Bandeira VARCHAR(100);
ALTER TABLE vendas_processadas MODIFY COLUMN Forma_de_pagamento VARCHAR(200);

-- Corrigir vendas_diversas
ALTER TABLE vendas_diversas MODIFY COLUMN Valor_da_venda DECIMAL(18,2);
ALTER TABLE vendas_diversas MODIFY COLUMN Valor_descontado DECIMAL(18,2);
ALTER TABLE vendas_diversas MODIFY COLUMN Valor_RR DECIMAL(18,2);
ALTER TABLE vendas_diversas MODIFY COLUMN Taxas_Perc DECIMAL(18,2);
ALTER TABLE vendas_diversas MODIFY COLUMN Taxas_RR DECIMAL(18,2);
ALTER TABLE vendas_diversas MODIFY COLUMN Valor_líquido_da_venda DECIMAL(18,2);
ALTER TABLE vendas_diversas MODIFY COLUMN Bandeira VARCHAR(100);
ALTER TABLE vendas_diversas MODIFY COLUMN Forma_de_pagamento VARCHAR(200);

-- Corrigir recebiveis_processados
ALTER TABLE recebiveis_processados MODIFY COLUMN valor_recebivel DECIMAL(18,2);
ALTER TABLE recebiveis_processados MODIFY COLUMN valor_liquido DECIMAL(18,2);

-- Corrigir recebiveis_filtrados
ALTER TABLE recebiveis_filtrados MODIFY COLUMN valor_recebivel DECIMAL(18,2);
ALTER TABLE recebiveis_filtrados MODIFY COLUMN valor_liquido DECIMAL(18,2);

-- Opcional: Arredondar valores existentes
UPDATE vendas_processadas SET 
    Valor_da_venda = ROUND(Valor_da_venda, 2),
    Valor_RR = ROUND(Valor_RR, 2),
    Taxas_Perc = ROUND(Taxas_Perc, 2),
    Taxas_RR = ROUND(Taxas_RR, 2);
```

---

## 🔸 Diretrizes Estruturais e de Documentação
- **conf/**: helpers DB, compatibilidade SQL dual (sempre criar MySQL e SQLite)
- **modules/**: views/UI (importação, gestão, analista, cálculos, relatórios, correção)
- **proc/**: processamento de arquivos, lógica de usuários
- **data/**: bancos SQLite, arquivos processados
- **requirements.txt**: dependências específicas
- **Sempre consultar README.md**, consolidar novidades nele,
  - jamais diluir informações em múltiplos markdowns!

---

## 🔸 FLUXO DE PROCESSAMENTO DE ARQUIVOS

### 📥 **1. IMPORTAÇÃO (modules/ui_importacao.py → proc/proc_importacao.py)**

#### **Etapa 1.1: Upload e Leitura do Arquivo**
```
UI: FileInput → btn_processar.on_click()
  ↓
safe_read_file(path) - Detecta encoding, trata arquivos corrompidos
  ↓
detectar_cabecalho(df) - Identifica linha de cabeçalho automaticamente
  ↓
preparar_dataframe_de_arquivo(df, contexto) - Aplica de-para de colunas
```

**Funções-chave:**
- `safe_read_file()`: Lê .xlsx/.xls/.csv com fallback de encoding
- `detectar_cabecalho()`: Detecta automaticamente linha de cabeçalho
- `is_multisheet_rede_file()`: Verifica se é arquivo multi-planilha REDE
- `safe_read_multisheet_file()`: Lê e consolida múltiplas abas

#### **Etapa 1.2: Aplicação de De-Para**
```
preparar_dataframe_de_arquivo(df, ec_id, contexto, tipo_arquivo)
  ↓
aplicar_regras_depara(engine, df, contexto, tipo_arquivo, ec_id)
  ↓
Carrega regras: depara_listar(engine, contexto, tipo_arquivo, ec_id)
  ↓
Aplica transformações:
  - tipo_preenchimento='importado' → Renomeia coluna origem → destino
  - tipo_preenchimento='padrão' → Preenche coluna com valor_padrao
  - tipo_preenchimento='sistema' → Adiciona cliente_id, ec_id, processamentoid
  - tipo_preenchimento='ignorar' → Remove coluna
```

**Resultado:** DataFrame com colunas padronizadas do sistema

---

### 🔄 **2. NORMALIZAÇÃO (proc/proc_importacao.py)**

#### **Etapa 2.1: Normalização de Vendas**
```
normalizar_dataframe_vendas(df, engine, ec_id, contexto, usuario, tipo_arquivo)
  ↓
1. Limpeza de valores infinitos (np.inf → np.nan)
  ↓
2. Preenchimento de 'Adquirente' baseado no contexto (CIELO, REDE, etc)
  ↓
3. Conversão de datas → datetime
   - Data_da_venda, Data_da_autorização_da_venda, Previsão_de_pagamento
  ↓
4. Conversão de valores monetários → float + ROUND(2) ⚠️ CRÍTICO
   - Taxas_Perc, Taxas_RR, Valor_da_venda, Valor_descontado, Valor_RR, Valor_líquido
   - SEMPRE: df[col] = _to_float_br(df[col]).round(2)
  ↓
5. Conversão de Quantidade_de_parcelas → int
  ↓
6. Cálculo de Valor_RR (se Taxas_RR existe)
   - df['Valor_RR'] = ((df['Valor_da_venda'] * df['Taxas_RR']) / 100).round(2) ⚠️
  ↓
7. Ajustes específicos REDE (multiplicar taxas por 100 se < 1)
  ↓
8. Adiciona colunas de metadados:
   - processamentoid (EC_SEQUENCIA - DATA)
   - cliente_id, ec_id
   - data_processamento, usuario_processamento
```

#### **Etapa 2.2: Normalização de Recebíveis**
```
normalizar_dataframe_recebiveis(df, engine, ec_id, contexto, usuario)
  ↓
1. Conversão de datas → datetime
   - data_pagamento, data_recebivel, data_processamento
  ↓
2. Conversão de valores monetários → numeric + ROUND(2) ⚠️ CRÍTICO
   - valor_recebivel, valor_liquido, valor_bruto, valor_taxa
   - SEMPRE: df[col] = pd.to_numeric(df[col], errors='coerce').round(2)
  ↓
3. Preenchimento de 'Adquirente' baseado no contexto
  ↓
4. Adiciona metadados (data_processamento, usuario_processamento)
```

**⚠️ REGRA CRÍTICA DE ARREDONDAMENTO:**
- **SEMPRE** aplicar `.round(2)` após conversões (_to_float_br, to_numeric)
- **SEMPRE** aplicar `.round(2)` após cálculos matemáticos
- **NUNCA** gravar valores sem arredondamento (causa 0.30 → 0.3097)

---

### 🔍 **3. CLASSIFICAÇÃO E FILTRAGEM**

#### **Etapa 3.1: Filtragem por Termos (Vendas)**
```
normalizar_dataframe_vendas() → Aplicação de filtros
  ↓
Carrega termos_filtraveis (engine, ec_id, contexto, tipo='v')
  ↓
Busca termos nas colunas:
  - Resumo_da_operação (prioridade)
  - status_da_venda (fallback)
  - Primeira coluna disponível
  ↓
Normaliza texto: unicodedata.normalize('NFKD') + upper() + strip()
  ↓
Marca registros: df['Filtrado'] = 1 (se termo encontrado)
  ↓
Retorna: (df_processadas, df_filtradas, df_diversas)
```

**Tabelas de Destino:**
- `vendas_processadas` - Registros válidos (Filtrado = 0)
- `vendas_filtradas` - Registros rejeitados (Filtrado = 1, termos encontrados)
- `vendas_diversas` - Casos especiais (flag manual ou lógica específica)

#### **Etapa 3.2: Filtragem por Termos (Recebíveis)**
```
normalizar_dataframe_recebiveis() → Aplicação de filtros
  ↓
Carrega termos_filtraveis (engine, ec_id, contexto, tipo='r')
  ↓
Busca termos nas colunas:
  - lancamento (prioridade)
  - descricao (fallback)
  - Primeira coluna disponível
  ↓
Marca registros: df['Filtrado'] = 1
  ↓
Retorna: DataFrame com coluna 'Filtrado'
```

**Separação posterior em:**
- `recebiveis_processados` (Filtrado = 0)
- `recebiveis_filtrados` (Filtrado = 1)

---

### 💾 **4. GRAVAÇÃO NO BANCO**

#### **Etapa 4.1: Gravação de Vendas**
```
classificar_e_gravar_vendas(engine, df, cliente_id, ec_id, processamentoid, usuario)
  ↓
1. Normaliza DataFrame
   - normalizar_dataframe_vendas(df, engine, ec_id, contexto, usuario, 'venda')
  ↓
2. Separa em 3 DataFrames
   - df_proc: Filtrado = 0 (vendas válidas)
   - df_filt: Filtrado = 1 (vendas rejeitadas)
   - df_div: (vendas diversas/casos especiais)
  ↓
3. Remove colunas internas (Filtrado, planilha_origem)
  ↓
4. Garante dtype DECIMAL para valores monetários ⚠️
  ↓
5. Bulk insert nas tabelas
   - vendas_processadas_bulk_insert(engine, df_proc)
   - vendas_filtradas_bulk_insert(engine, df_filt)
   - vendas_diversas_bulk_insert(engine, df_div)
  ↓
Retorna: (qtd_proc, qtd_filt, qtd_div)
```

#### **Etapa 4.2: Gravação de Recebíveis**
```
classificar_e_gravar_recebiveis(engine, df, cliente_id, ec_id, processamentoid, usuario)
  ↓
1. Normaliza DataFrame
   - normalizar_dataframe_recebiveis(df, engine, ec_id, contexto, usuario)
  ↓
2. Separa por coluna 'Filtrado'
   - df_proc: Filtrado = 0
   - df_filt: Filtrado = 1
  ↓
3. Remove colunas internas
  ↓
4. Converte valores monetários + ROUND(2) ⚠️
   - df[col] = pd.to_numeric(df[col], errors='coerce').round(2)
  ↓
5. Bulk insert nas tabelas
   - recebiveis_processados_bulk_insert(engine, df_proc)
   - recebiveis_filtrados_bulk_insert(engine, df_filt)
  ↓
Retorna: (qtd_proc, qtd_filt)
```

#### **Etapa 4.3: Bulk Insert (conf/funcoesbd.py)**
```
vendas_processadas_bulk_insert(engine, df)
  ↓
Especifica dtype para DECIMAL ⚠️ CRÍTICO:
  dtype_map = {
      'Valor_da_venda': DECIMAL(18, 2),
      'Valor_descontado': DECIMAL(18, 2),
      'Valor_RR': DECIMAL(18, 2),
      'Taxas_Perc': DECIMAL(18, 2),
      'Taxas_RR': DECIMAL(18, 2),
      'Valor_líquido_da_venda': DECIMAL(18, 2),
  }
  ↓
df.to_sql(
    name='vendas_processadas',
    con=engine,
    dtype=dtype_map,  ⚠️ Obrigatório!
    if_exists='append',
    index=False,
    method='multi'
)
```

**⚠️ REGRA CRÍTICA:**
- **SEMPRE** especificar `dtype` com DECIMAL(18,2) para valores monetários
- **NUNCA** deixar Pandas inferir tipos (inferirá DOUBLE)

---

### 🔄 **5. CONTROLE DE PROCESSAMENTO**

#### **ProcessamentoID**
```
Formato: "EC_SEQUENCIA - DATA"
Exemplo: "1068306022_0001 - 09/12/2025 08:13:30"

Geração:
  processamento_gerar_novo_id(engine, ec_id, datetime.now())
    ↓
  Consulta sequência atual: SELECT MAX(id_processamento) FROM controle_processamentos
    ↓
  Incrementa: sequencia + 1
    ↓
  Formata: f"{ec_id}_{sequencia:04d} - {data:%d/%m/%Y %H:%M:%S}"

Gravação:
  processamento_salvar(engine, ec_id, cliente_id, processamentoid, descricao, data_proc)
    ↓
  INSERT INTO controle_processamentos (id_processamento, cliente_id, ec_id, data_processamento)
```

#### **Continuar Processamento Anterior**
```
UI: continuar_checkbox.value = True
  ↓
Usa processamentoid_select.value (existente)
  ↓
TODAS as vendas/recebíveis usam MESMO processamentoid
  ↓
Permite agrupar múltiplos arquivos em um único processamento
```

---

### 📊 **6. FLUXO COMPLETO RESUMIDO**

```
┌─────────────────────────────────────────────────────────────────┐
│ 1. UPLOAD                                                       │
│    FileInput → safe_read_file → detectar_cabecalho             │
└────────────────┬────────────────────────────────────────────────┘
                 ↓
┌─────────────────────────────────────────────────────────────────┐
│ 2. DE-PARA                                                      │
│    aplicar_regras_depara → Renomeia colunas                    │
│    Adiciona colunas sistema (cliente_id, ec_id, processamentoid)│
└────────────────┬────────────────────────────────────────────────┘
                 ↓
┌─────────────────────────────────────────────────────────────────┐
│ 3. NORMALIZAÇÃO                                                 │
│    ⚠️ Converte datas → datetime                                 │
│    ⚠️ Converte valores → float/numeric + .round(2)              │
│    ⚠️ Calcula Valor_RR + .round(2)                              │
│    Preenche Adquirente (contexto)                              │
└────────────────┬────────────────────────────────────────────────┘
                 ↓
┌─────────────────────────────────────────────────────────────────┐
│ 4. FILTRAGEM                                                    │
│    Carrega termos_filtraveis                                   │
│    Marca df['Filtrado'] = 1 se termo encontrado               │
│    Separa: processadas (0) vs filtradas (1)                   │
└────────────────┬────────────────────────────────────────────────┘
                 ↓
┌─────────────────────────────────────────────────────────────────┐
│ 5. GRAVAÇÃO                                                     │
│    ⚠️ dtype={'Valor_RR': DECIMAL(18,2), ...}                    │
│    bulk_insert → vendas_processadas / vendas_filtradas        │
│    bulk_insert → recebiveis_processados / recebiveis_filtrados│
└─────────────────────────────────────────────────────────────────┘
```

---

### ⚠️ **PONTOS CRÍTICOS DE ATENÇÃO**

1. **Arredondamento Obrigatório:**
   - Após `_to_float_br()` → `.round(2)`
   - Após `pd.to_numeric()` → `.round(2)`
   - Após cálculos matemáticos → `.round(2)`

2. **dtype Obrigatório:**
   - Sempre especificar em `df.to_sql(dtype=dtype_map)`
   - Valores monetários: `DECIMAL(18, 2)`

3. **Ordem de Operações:**
   - Converter → Arredondar → Gravar
   - NUNCA: Converter → Gravar (sem arredondar)

4. **Validação de Dados:**
   - Remover np.inf antes de conversões
   - Tratar np.nan adequadamente
   - Validar datas com `dayfirst=True`

5. **Processamento Multi-Arquivo:**
   - Mesmo processamentoid para múltiplos arquivos
   - Consolidação via controle_processamentos

---

## 🔸 REGRAS PARA O AGENTE IA

### 1. Queries/Helpers: Sempre prover MySQL e SQLite
- Toda função SQL deve prever ambos os bancos via helpers.
- Siga exemplos nas funções _is_sqlite, _concat, _year etc (conf/)
- Parametrização: `%s`, `%(param)s` (MySQL), `:param` (SQLite)
- **MySQL**: Use `MODIFY COLUMN` para ALTER TABLE (não `ALTER COLUMN`)
- EXEMPLO:
```python
def _year(engine, column):
    return f"strftime('%Y', {column})" if _is_sqlite(engine) else f"YEAR({column})"
```

### 2. Tipos de Dados - CRÍTICO
- **Valores monetários**: SEMPRE usar `DECIMAL(18,2)` no dtype do pandas to_sql
- **Percentuais/Taxas**: SEMPRE usar `DECIMAL(18,2)`
- **NUNCA usar DOUBLE/FLOAT** para dinheiro (causa imprecisão de ponto flutuante)
- Exemplo correto em bulk_insert:
```python
from sqlalchemy.types import DECIMAL

dtype_map = {
    'Valor_da_venda': DECIMAL(18, 2),
    'Taxas_Perc': DECIMAL(18, 2),
    'Valor_RR': DECIMAL(18, 2),
}
df.to_sql(..., dtype=dtype_map)
```

### 3. Gestão de Taxas - Lógica Hierárquica
- **Sistema de 3 camadas** para cálculo de taxas:
  1. **Específica**: Taxa com forma_pagamento + bandeira (WHERE bandeira IS NOT NULL)
  2. **Genérica**: Taxa só com forma_pagamento (WHERE bandeira IS NULL) 
  3. **LOG**: Taxa mínima do período (fallback quando não há cadastro)
- Aplicar camadas sequencialmente (específica primeiro, genérica depois)
- Taxa genérica aplica-se a TODAS as bandeiras quando bandeira = NULL
- UI deve permitir cadastro de taxa genérica (checkbox desabilita campo bandeira)

### 4. SQL Pandas/Resultados:
- Sempre use acesso dinâmico às colunas (`result.columns`) ao usar Pandas.
- Nunca usar string fixa: `result["coluna"]` (pode falhar pela sensibilidade de case no SQLite).
- Use alias explícito em queries.

### 5. Funções e nomenclatura
- Snake_case para variáveis, argumentos e funções.
- Sempre docstring clara e breve (em português).
- Metodologia bulk_insert padronizada para tabelas processadas.
- Sempre especificar dtype para colunas DECIMAL ao usar to_sql()

### 6. UI/Panel
- Widgets via helpers.
- Mensagens via `_notify("success"|"error"|"warning", msg)`.
- Modularizar views por contexto de negócio.
- Checkbox para taxa genérica deve desabilitar campo bandeira quando marcado
- MultiChoice para seleção de múltiplos ECs (copiar taxas, etc)

### 7. Documentação/Checklist
- Toda novidade ou exemplo deve ser adicionado no `README.md` principal.
- Novas funcionalidades? Informe dual path (MySQL/SQLite) e que foi testado em ambos.
- Adotar checklist padrão para qualquer função nova:
  - `README.md` atualizado
  - Docstring presente e explicativa
  - Compatível igualmente para ambos os bancos
  - Testado no UI (panel)
  - Tipos DECIMAL especificados para valores monetários

---

## 🔸 Exemplo de Padrão
```python
def _year(engine, column):
    """Retorna expressão SQL para extrair ano (compatível).
    Args: engine (sqlalchemy.Engine), column (str)
    Returns: str
    """
    return f"strftime('%Y', {column})" if _is_sqlite(engine) else f"YEAR({column})"

# Exemplo correto de bulk_insert com DECIMAL
def vendas_processadas_bulk_insert(engine: Engine, df) -> int:
    from sqlalchemy.types import DECIMAL
    
    dtype_map = {
        'Valor_da_venda': DECIMAL(18, 2),
        'Valor_descontado': DECIMAL(18, 2),
        'Valor_RR': DECIMAL(18, 2),
        'Taxas_Perc': DECIMAL(18, 2),
    }
    
    df.to_sql(
        name="vendas_processadas",
        con=engine,
        dtype=dtype_map,
        if_exists="append"
    )
    return len(df)

# Exemplo correto de cálculo com arredondamento
def normalizar_valores_monetarios(df: pd.DataFrame) -> pd.DataFrame:
    """Normaliza valores monetários com precisão decimal correta"""
    
    # ⚠️ CRÍTICO: SEMPRE usar .round(2) após conversões
    for col in ['Valor_da_venda', 'Taxas_Perc', 'Valor_RR']:
        if col in df.columns:
            df[col] = _to_float_br(df[col]).round(2)
    
    # ⚠️ CRÍTICO: SEMPRE usar .round(2) após cálculos
    if 'Taxas_RR' in df.columns and 'Valor_da_venda' in df.columns:
        df['Valor_RR'] = ((df['Valor_da_venda'] * df['Taxas_RR']) / 100).round(2)
    
    return df
```

---

## 🔸 Convenções Gerais
- Comentários explicativos para TODO trecho não trivial.
- Views separando claramente interface, processamento e banco.
- Estrutura de funções seguindo mesmo padrão para processadas, filtradas, deduplicação e agregação (conf/).
- Scripts/funcionais acessórios claros em dev_tools/ ou scripts/
- Sempre manter nomes de variáveis e argumentos com clareza para facilitar busca e manutenção.
- Padronização dos nomes de colunas conforme já usado no projeto.

---

## 🔸 Referência para Novos SQL
- **Banco principal**: MySQL (não MSSQL!)
- Placeholders: `%s`, `%(param)s` (MySQL), `:param` (SQLite)
- Datas: `DATE_FORMAT()` (MySQL), `strftime()` (SQLite)
- Concat: `CONCAT()` (MySQL), `||` (SQLite)
- INSERT IGNORE: `INSERT IGNORE` (MySQL), `INSERT OR IGNORE` (SQLite)
- UPSERT: `ON DUPLICATE KEY UPDATE` (MySQL), `INSERT OR REPLACE` (SQLite)
- **ALTER TABLE**: `MODIFY COLUMN` (MySQL), `ALTER COLUMN` (SQLite/outros)
- Aggregação com GROUP BY: Sempre usar `ANY_VALUE()` para colunas não agregadas (MySQL 8.0+ ONLY_FULL_GROUP_BY)

---

## 🔸 Checklist para Novas Features IA
- [ ] Novo código SQL teve ambos bancos implementados?
- [ ] Novo helper/documentação/roteiro está no README.md?
- [ ] Função e parâmetros com docstring?
- [ ] Caso use Pandas, está acessando colunas de forma dinâmica?
- [ ] Nome de variáveis está claro?
- [ ] Lógica complexa foi comentada?
- [ ] Testes manuais feitos nos dois modos (MySQL/SQLite)?
- [ ] **Valores monetários usando DECIMAL(18,2) não DOUBLE?**
- [ ] **dtype especificado em df.to_sql() para colunas decimais?**
- [ ] Taxas hierárquicas (específica → genérica → LOG) implementadas corretamente?
- [ ] UI permite cadastro de taxas genéricas (bandeira NULL)?

---

## 🔸 Armadilhas Comuns - EVITAR

### ❌ NUNCA FAZER:
1. **Usar DOUBLE/FLOAT para valores monetários**
   - Causa: 0.30 vira 0.30000000000000004 ou 0.3097
   - Solução: DECIMAL(18,2)

2. **Confundir MySQL com MSSQL**
   - MySQL usa: `MODIFY COLUMN`
   - MSSQL usa: `ALTER COLUMN`

3. **Esquecer dtype no to_sql()**
   - Pandas infere tipos incorretos (DOUBLE em vez de DECIMAL)
   - Sempre especificar: `dtype={'Valor_RR': DECIMAL(18,2)}`

4. **Criar múltiplos arquivos de documentação**
   - Sempre consolidar no README.md principal

5. **Esquecer ANY_VALUE() em GROUP BY (MySQL 8.0+)**
   - Erro: "not in GROUP BY clause"
   - Solução: `ANY_VALUE(bandeira)` para colunas não agregadas

6. **Esquecer .round(2) em cálculos monetários no código Python**
   - Problema: Mesmo com DECIMAL no banco, cálculos intermediários em Python geram imprecisão
   - Causa: 0.30 vira 0.3097 durante operações matemáticas
   - Exemplo errado: `df['Valor_RR'] = (df['Valor'] * df['Taxa']) / 100`
   - Exemplo correto: `df['Valor_RR'] = ((df['Valor'] * df['Taxa']) / 100).round(2)`
   - Onde aplicar: 
     - Após TODOS os cálculos (multiplicação, divisão, etc)
     - Após conversões com `_to_float_br()` ou `pd.to_numeric()`
     - Antes de gravar no banco com `to_sql()`
   - Padrão: `.round(2)` encadeado imediatamente após operação

7. **Esquecer de calcular perda quando valor calculado é zero**
   - Problema: Quando `tem_receba_rapido = False`, perda_rr fica 0.00 mesmo havendo cobrança no arquivo
   - Causa: Sistema zera `tx_rr_calc` e `vl_rr_calc`, mas deveria calcular economia
   - Exemplo errado: `perda_rr = 0` quando cliente não usa RR
   - Exemplo correto: `perda_rr = -vl_rr_venda` (economia por não usar RR)
   - Onde aplicar: Sempre que desabilitar funcionalidade mas houver valores no arquivo original
   - Lógica: Se não usa funcionalidade MAS foi cobrado = economia (valor negativo)

8. **Usar variáveis antes de defini-las**
   - Problema: `periodo_ini_sql` usado mas não definido, causa NameError
   - Causa: Variável depende de lógica condicional mas não é inicializada
   - Exemplo errado: Usar `periodo_ini_sql` sem definir baseado em `tipo_taxa`
   - Exemplo correto: 
     ```python
     # Definir ANTES de usar
     if tipo_taxa == "log_mensal":
         periodo_ini_sql = "DATE_FORMAT(vp.Data_da_venda, '%Y-%m-01')"
     elif tipo_taxa == "log_trimestral":
         periodo_ini_sql = "DATE_FORMAT(vp.Data_da_venda, '%Y-Q')"
     # ... usar depois
     query = f"... {periodo_ini_sql} ..."
     ```
   - Onde aplicar: SEMPRE inicializar variáveis antes do primeiro uso
   - Padrão: Definir no início do bloco lógico onde será usada

9. **Inserir variável SQL completa dentro de f-string**
   - Problema: `periodo_ini_sql` contém `DATE_FORMAT(vp.Data_da_venda, '%Y-01-01')` e é inserido em f-string, gerando `DATE_FORMAT(..., 'DATE_FORMAT(...)')`
   - Causa: Variável já contém expressão SQL completa, mas é tratada como formato simples

10. **Esquecer de passar parâmetros para conn.execute() com text()**
   - Problema: Query usa `:calc_id` e `:calc_tipo` mas `conn.execute(text(sql))` não recebe parâmetros
   - Causa: text() apenas prepara query, mas parâmetros precisam ser passados separadamente
   - Exemplo errado: `conn.execute(text("... WHERE calc_id = :calc_id"))`
   - Exemplo correto: `conn.execute(text("... WHERE calc_id = :calc_id"), {"calc_id": proc_id, "calc_tipo": tipo_taxa})`
   - Onde aplicar: **TODA** query com parâmetros nomeados (`:param`)
   - Resultado: Sem parâmetros, query falha silenciosamente ou retorna 0 rows
   - Debug: Sempre verificar `result.rowcount` após UPDATE/INSERT
   - Exemplo errado:
     ```python
     periodo_ini_sql = "DATE_FORMAT(vp.Data_da_venda, '%Y-01-01')"
     query = f"... DATE_FORMAT(vp2.Data_da_venda, '{periodo_ini_sql}') ..."
     # Gera: DATE_FORMAT(vp2.Data_da_venda, 'DATE_FORMAT(vp.Data_da_venda, '%Y-01-01')')
     ```
   - Exemplo correto:
     ```python
     periodo_format = "%Y-01-01"  # Apenas o formato
     periodo_ini_sql = "DATE_FORMAT(vp.Data_da_venda, '%Y-01-01')"  # SQL completo
     query = f"... DATE_FORMAT(vp2.Data_da_venda, '{periodo_format}') ..."
     # Gera: DATE_FORMAT(vp2.Data_da_venda, '%Y-01-01') ✅
     ```
   - Onde aplicar: Separar formato (string simples) de expressão SQL completa
   - Padrão: Criar duas variáveis - uma para formato, outra para SQL completo

11. **Loop de batching desnecessário para UPDATEs com agregação**
   - Problema: Buscar IDs → Loop 10k → Montar IN clause → UPDATE parcial
   - Causa: Overhead de múltiplas queries quando MySQL pode agregar tudo de uma vez
   - Exemplo errado:
     ```python
     ids = SELECT id WHERE tx_calc IS NULL
     for batch in chunks(ids, 10000):
         ids_str = ",".join(str(x) for x in batch)
         UPDATE ... WHERE id IN (ids_str) AND tx_calc IS NULL
     ```
   - Exemplo correto:
     ```python
     UPDATE vendas_calculos vc
     JOIN vendas_processadas vp ON vc.id_venda = vp.id
     JOIN (
         SELECT periodo, forma, bandeira, MIN(tx_venda) AS min_tx
         FROM vendas_calculos vc2
         JOIN vendas_processadas vp2 ON vc2.id_venda = vp2.id
         WHERE calc_id = X AND calc_tipo = Y
         GROUP BY periodo, forma, bandeira
     ) agg ON agg.periodo = periodo AND agg.forma = vc.forma AND agg.bandeira = vc.bandeira
     SET vc.tx_calc = agg.min_tx
     WHERE calc_id = X AND calc_tipo = Y AND tx_calc IS NULL
     ```
   - Onde aplicar: UPDATEs com agregação MIN/MAX/AVG em datasets grandes
   - Benefícios: 1 query vs 100+, transação única, código mais simples (80+ linhas → 30 linhas)
   - Performance: Elimina overhead de loop Python e múltiplas queries SQL

### ✅ SEMPRE FAZER:
1. Verificar se banco é MySQL ou SQLite antes de sugerir SQL
2. Especificar DECIMAL para todas colunas monetárias (schema + dtype)
3. Aplicar `.round(2)` após TODOS os cálculos e conversões monetárias
4. Testar com dados reais (0.30 deve permanecer 0.30 em TODA a pipeline)
5. Implementar lógica hierárquica de taxas (específica → genérica → LOG)
6. Adicionar debug logging para queries complexas
7. Comentar código com ⚠️ CRÍTICO onde há risco de imprecisão decimal
8. Definir variáveis de período ANTES de usar em queries dinâmicas
9. Validar que funções recebem parâmetros corretos (tipo_taxa, etc)
10. **SEMPRE passar dict de parâmetros em conn.execute(text(sql), params)** quando SQL usa `:param`
11. **SEMPRE verificar result.rowcount após UPDATE/INSERT** para confirmar que query funcionou

---

## 🔸 Padrão de Cálculo de Período LOG

O sistema de taxas LOG usa diferentes períodos de agregação baseado no `tipo_taxa`:

### Formatos de Período
```python
# Definição de periodo_ini_sql baseado no tipo_taxa
if tipo_taxa == "log_mensal":
    periodo_ini_sql = "DATE_FORMAT(vp.Data_da_venda, '%Y-%m-01')"  # Agrupa por mês
elif tipo_taxa == "log_trimestral":
    periodo_ini_sql = "DATE_FORMAT(vp.Data_da_venda, '%Y-Q')"      # Agrupa por trimestre
elif tipo_taxa == "log_semestral":
    periodo_ini_sql = "DATE_FORMAT(vp.Data_da_venda, '%Y-S')"      # Agrupa por semestre
else:  # log_anual (padrão)
    periodo_ini_sql = "DATE_FORMAT(vp.Data_da_venda, '%Y-01-01')"  # Agrupa por ano
```

### Uso em Queries
```python
# Exemplo de query com período dinâmico
query = f"""
    SELECT 
        ec_id,
        bandeira,
        forma_pagamento,
        {periodo_ini_sql} AS periodo_ini,
        MIN(Taxas_Perc) AS min_taxa
    FROM vendas_processadas
    GROUP BY ec_id, bandeira, forma_pagamento, periodo_ini
"""
```

### ⚠️ REGRAS CRÍTICAS
1. **SEMPRE** definir `periodo_format` E `periodo_ini_sql` ANTES de usar
2. **NUNCA** inserir `periodo_ini_sql` (SQL completo) dentro de DATE_FORMAT em f-string
3. **USAR** `periodo_format` (string simples) em queries dinâmicas
4. **USAR** `periodo_ini_sql` (SQL completo) apenas para substituição direta sem DATE_FORMAT
5. **SEMPRE** usar o mesmo formato na subquery e no JOIN
6. **SEMPRE** passar `tipo_taxa` para funções que calculam LOG
7. Batch updates devem usar período dinâmico (não hardcoded)
8. **NUNCA** filtrar `tx_calc IS NULL` na subquery de agregação LOG - deve calcular MIN de TODAS as vendas do período
   - ❌ Errado: `WHERE calc_id = X AND calc_tipo = Y AND tx_calc IS NULL` na subquery
   - ✅ Correto: `WHERE calc_id = X AND calc_tipo = Y` na subquery (sem filtro tx_calc)
   - Motivo: Agregação MIN deve considerar TODAS as vendas do período para encontrar menor taxa
   - Filtro `tx_calc IS NULL` só deve estar no WHERE principal do UPDATE (define quais registros atualizar)

---

## 🔸 Fluxo de Telas/Pontos-Chave
- Login → Menu lateral → escolha de função/view em Panel/Tabs
- Importação/De-Para
- Gestão de entidades (clientes, bandeiras, taxas)
  - **Taxas**: Permite cadastro genérico (bandeira NULL) e específico
  - **Copiar taxas**: MultiChoice para copiar de um EC para múltiplos destinos
- Interface de cálculo/análise, visualização tabular e gráficos
- Correção retroativa (formas/bandeiras) sempre registrando no log
- Consistência de interface para todos módulos

---

## 🔸 Contexto de Negócio - Taxas

### Sistema Hierárquico de Taxas (3 Camadas)
1. **Taxa Específica** (prioridade ALTA)
   - WHERE bandeira IS NOT NULL AND forma_pagamento = X AND bandeira = Y
   - Exemplo: DÉBITO + VISA = 2.0%

2. **Taxa Genérica** (prioridade MÉDIA)
   - WHERE bandeira IS NULL AND forma_pagamento = X
   - Exemplo: DÉBITO (todas bandeiras) = 2.5%
   - UI: Checkbox "Taxa Genérica" desabilita campo bandeira

3. **Taxa LOG** (prioridade BAIXA - fallback)
   - MIN(taxa) do período quando não há cadastro
   - Usado apenas quando camadas 1 e 2 não encontram taxa

### Implementação de Cálculo
```python
# Camada 1: Específica
UPDATE vendas_calculadas vc
JOIN taxas t ON t.forma_pagamento = vc.forma AND t.bandeira = vc.bandeira
SET vc.tx_calc = t.taxa
WHERE t.bandeira IS NOT NULL

# Camada 2: Genérica (apenas onde ainda não calculou)
UPDATE vendas_calculadas vc
JOIN taxas t ON t.forma_pagamento = vc.forma
SET vc.tx_calc = t.taxa
WHERE t.bandeira IS NULL AND vc.tx_calc IS NULL

# Camada 3: LOG (fallback)
UPDATE vendas_calculadas vc
SET vc.tx_calc = (SELECT MIN(taxa) FROM vendas_periodo WHERE forma = vc.forma)
WHERE vc.tx_calc IS NULL
```

---

## IMPORTANTE
- **Banco é MySQL, não MSSQL!** Sempre confirmar sintaxe correta
- Nunca sugerir SQL "puro" MySQL sem fallback SQLite!
- Toda lógica implementada **deve** prever equivalência, via helpers ou nova função dual
- **DECIMAL(18,2) obrigatório** para valores monetários (nunca DOUBLE/FLOAT)
- **dtype obrigatório** em df.to_sql() para colunas decimais
- Sistema de taxas usa 3 camadas hierárquicas (específica → genérica → LOG)
- Sugerir inclusão ou melhoria no README sempre!
- Manter código claro, modular, autoexplicativo, comentado e aderente a essas práticas
- Debug logging para queries complexas e cálculos multi-camada

---

## 🔸 Resolução Rápida de Problemas

| Problema | Causa | Solução |
|----------|-------|---------|
| 0.30 vira 0.3097 (BD) | DOUBLE em vez de DECIMAL no schema | `ALTER TABLE ... MODIFY COLUMN ... DECIMAL(18,2)` |
| 0.30 vira 0.3097 (código) | Falta .round(2) em cálculos Python | Adicionar `.round(2)` após cálculos e conversões |
| dtype não especificado | Pandas infere DOUBLE | `dtype={'col': DECIMAL(18,2)}` em to_sql() |
| "not in GROUP BY" | MySQL ONLY_FULL_GROUP_BY | `ANY_VALUE(coluna)` |
| Taxa não aplicada | Ordem hierárquica errada | Específica → Genérica → LOG |
| ALTER TABLE falha | Sintaxe MSSQL no MySQL | `MODIFY COLUMN` não `ALTER COLUMN` |
| Valores arredondados | Falta precisão decimal | Verificar estrutura da tabela (DOUBLE→DECIMAL) |
| perda_rr sempre 0.00 | Zerou tx_rr_calc sem calcular economia | `perda_rr = -vl_rr_venda` quando não usa RR |
| Variável não definida | Uso antes de declaração | Definir variável ANTES de usar (ex: `periodo_ini_sql`) |
| periodo_ini_sql undefined | Falta definição por tipo_taxa | Definir baseado em tipo_taxa antes de usar em queries RR |
| DATE_FORMAT duplicado | periodo_ini_sql inserido em f-string dentro de DATE_FORMAT | Usar `periodo_format` (string) não `periodo_ini_sql` (SQL completo) |
| SQL: "Incorrect parameters" | Variável SQL completa usada como parâmetro de função | Separar formato de expressão SQL completa |
| UPDATE retorna 0 rows | Faltam parâmetros em conn.execute() | Passar dict: `conn.execute(text(sql), {"calc_id": x, "calc_tipo": y})` |
| tx_calc sempre NULL | Query LOG sem parâmetros | Adicionar params em execute() e verificar result.rowcount |

---

## ✅ Checklist de Compatibilidade MySQL/SQLite

Ao criar ou modificar funções que executam SQL, **SEMPRE** verificar:

### 🔍 Verificações Obrigatórias

- [ ] **Funções SQL Adapter têm `engine` como primeiro parâmetro?**
  - ✅ `_normalize_text_compare(engine, column, param)`
  - ❌ `_normalize_text_compare(column, param)` 

- [ ] **SQL usa helpers em vez de sintaxe específica?**
  - ✅ `_current_timestamp_sql(engine)` ou `CURRENT_TIMESTAMP`
  - ❌ `NOW()` (só MySQL)
  
- [ ] **INSERT IGNORE está adaptado?**
  - ✅ Usar `_insert_ignore_sql(engine, ...)` ou deixar `_adapt_sql()` converter
  - ❌ `INSERT IGNORE` direto (só MySQL)

- [ ] **Comparações de texto são case-insensitive quando necessário?**
  - ✅ `UPPER(contexto) = UPPER(:ctx)` ou `_normalize_text_compare()`
  - ❌ `contexto = :ctx` (case-sensitive no SQLite)

- [ ] **Concatenação usa helper?**
  - ✅ `_concat_sql(engine, 'a', 'b', 'c')`
  - ❌ `CONCAT('a', 'b', 'c')` (só MySQL)

- [ ] **Formatação de data usa helper?**
  - ✅ `_date_format_sql(engine, col, '%Y-%m')`
  - ❌ `DATE_FORMAT(col, '%Y-%m')` (só MySQL)

- [ ] **Strings vazias vs NULL estão corretas?**
  - ✅ `if descricao is not None` (preserva string vazia)
  - ❌ `if descricao` (string vazia = False)

- [ ] **Tipos DECIMAL estão corretos?**
  - ✅ `DECIMAL(18,2)` para valores monetários
  - ❌ `DOUBLE` ou `FLOAT` (imprecisão)

### 🧪 Testes Recomendados

Quando possível, testar em ambos os bancos:
```python
# Teste rápido de compatibilidade
from conf.db_manager import get_engine
engine = get_engine()  # Vai pegar MySQL ou SQLite baseado na config

# Se precisar testar específico:
# MySQL: configurar DB_TYPE=mysql em .env
# SQLite: configurar DB_TYPE=sqlite em .env
```

---


## 🔸 ORIENTAÇÃO: ALTERAÇÃO DIRETA NO CÓDIGO E EXPLICAÇÃO DETALHADA

**Sempre que o agente realizar uma alteração no código-fonte:**

1. **Alteração direta:**
  - A modificação deve ser feita diretamente no(s) arquivo(s) relevante(s) do projeto, utilizando as ferramentas apropriadas.
2. **Explicação detalhada na conversa:**
  - O agente deve explicar claramente na conversa:
    - O que foi alterado (arquivo, função, bloco de código)
    - O motivo da alteração e o problema/endereço
    - Como a mudança segue as regras do projeto (ex: DECIMAL, .round(2), hierarquia de taxas, dual path SQL, etc)
    - O impacto esperado e relação com requisitos críticos
3. **Checklist:**
  - Indicar se a alteração segue o checklist do agent.md (docstring, dual path, dtype, etc)
4. **Sugestão de documentação:**
  - Quando relevante, sugerir texto para README.md ou agent.md, consolidando a lição aprendida ou novo padrão.

**Objetivo:** Garantir rastreabilidade, clareza e aderência total às regras do projeto em cada alteração feita pelo agente.

---
## 🔸 META-INSTRUÇÃO: EVOLUÇÃO CONTÍNUA DO AGENTE

**REGRA CRÍTICA**: Ao final de cada interação significativa com o usuário:

1. **SEMPRE perguntar**: "Alguma lição aprendida nesta interação que deva ser adicionada ao agent.md?"
2. **SEMPRE documentar**:
   - Problemas encontrados e soluções aplicadas
   - Padrões novos descobertos
   - Armadilhas evitadas
   - Melhorias de código implementadas
   - Conhecimento específico do domínio

3. **SEMPRE atualizar** as seções relevantes:
   - ✅ SEMPRE FAZER / ❌ NUNCA FAZER
   - Resolução Rápida de Problemas (tabela)
   - Exemplos de código
   - Checklist para novas features
   - Estrutura de tabelas (se alterada)

4. **SEMPRE validar** que a nova informação:
   - É factual e foi testada
   - Não contradiz regras existentes
   - Está na seção correta
   - Usa linguagem clara e direta

### Exemplo de Atualização

Após resolver problema de arredondamento (0.30 → 0.3097):

```markdown
## Armadilhas Comuns - EVITAR

### ❌ NUNCA FAZER:
6. **Esquecer .round(2) em cálculos monetários**
   - Problema: Cálculos sem arredondamento geram imprecisão
   - Exemplo errado: `df['Valor_RR'] = (df['Valor'] * df['Taxa']) / 100`
   - Exemplo correto: `df['Valor_RR'] = ((df['Valor'] * df['Taxa']) / 100).round(2)`
   - Onde aplicar: TODOS os cálculos monetários no código Python
```

**OBJETIVO**: Transformar cada conversa em conhecimento permanente, criando documentação viva que previne repetição de erros e acelera desenvolvimento futuro.

---

> Última atualização: Dez/2025 (inclui lições de taxas genéricas, DECIMAL vs DOUBLE, hierarquia de cálculo)
