# Compatibilidade MySQL ↔ SQLite

## 📋 Resumo de Diferenças Corrigidas

Este documento lista todas as incompatibilidades entre MySQL e SQLite que foram identificadas e corrigidas no sistema Financial Checker.

---

## 🔧 1. Placeholders de Parâmetros

### Problema
- **MySQL**: Usa `%(param)s` ou `%s`
- **SQLite**: Usa `:param` ou `?`

### Solução
```python
if _is_sqlite(engine):
    query = "SELECT * FROM tabela WHERE id = :param"
else:
    query = "SELECT * FROM tabela WHERE id = %(param)s"

result = pd.read_sql(query, conn, params={"param": valor})
```

### Arquivos Corrigidos
- ✅ `modules/reports.py` - linha 507-530 (obter_adquirentes_distintos_processamento)

---

## 🔧 2. Funções de Data

### Problema
- **MySQL**: `DATE_FORMAT(coluna, formato)`
- **SQLite**: `strftime(formato, coluna)`

### Solução
```python
if _is_sqlite(engine):
    query = "SELECT strftime('%Y-%m', Data_da_venda) as MesAno FROM vendas"
else:
    query = "SELECT DATE_FORMAT(Data_da_venda, '%Y-%m') as MesAno FROM vendas"
```

### Arquivos Corrigidos
- ✅ `modules/ui_calculos.py` - linhas 354-385 (cálculo de períodos)
- ✅ `modules/grafico_views.py` - linha 33 (get_vendas_por_mes)

---

## 🔧 3. Concatenação de Strings

### Problema
- **MySQL**: `CONCAT(str1, str2, str3)`
- **SQLite**: `str1 || str2 || str3`

### Solução
```python
if _is_sqlite(engine):
    periodo_sql = "strftime('%Y', vp.Data_da_venda) || '-01-01'"
else:
    periodo_sql = "CONCAT(YEAR(vp.Data_da_venda), '-01-01')"
```

### Arquivos Corrigidos
- ✅ `modules/ui_calculos.py` - linhas 362-366 (concatenação de datas para períodos)

---

## 🔧 4. INSERT IGNORE

### Problema
- **MySQL**: `INSERT IGNORE INTO tabela ...`
- **SQLite**: `INSERT OR IGNORE INTO tabela ...`

### Solução
```python
def _insert_ignore_sql(engine, table, columns, values):
    if _is_sqlite(engine):
        return f"INSERT OR IGNORE INTO {table} ({columns}) VALUES ({values})"
    else:
        return f"INSERT IGNORE INTO {table} ({columns}) VALUES ({values})"
```

### Arquivos Corrigidos
- ✅ `conf/funcoesbd.py` - funções de inserção (ecs, termos, etc)

---

## 🔧 5. UPSERT (ON DUPLICATE KEY UPDATE)

### Problema
- **MySQL**: `INSERT ... ON DUPLICATE KEY UPDATE col=val`
- **SQLite**: `INSERT OR REPLACE INTO ...` ou `INSERT ... ON CONFLICT DO UPDATE`

### Solução
```python
def _upsert_sql(engine, insert_sql, update_clause):
    if _is_sqlite(engine):
        # SQLite usa INSERT OR REPLACE
        return insert_sql.replace("INSERT INTO", "INSERT OR REPLACE INTO")
    else:
        # MySQL usa ON DUPLICATE KEY UPDATE
        return f"{insert_sql} ON DUPLICATE KEY UPDATE {update_clause}"
```

### Arquivos Corrigidos
- ✅ `conf/funcoesbd.py` - inserção de clientes, endereços, contatos, dados bancários

---

## 🔧 6. Case-Sensitivity de Nomes de Colunas

### Problema Crítico ⚠️
- **MySQL**: Retorna nomes de colunas em **lowercase**, case-insensitive
- **SQLite**: **Preserva o case** do schema original (ex: `Adquirente`, `Lancamento`)

### Exemplo do Erro
```python
# ❌ ERRADO - Falha no SQLite se a coluna no schema é 'Adquirente'
result = pd.read_sql("SELECT adquirente FROM vendas_processadas", engine)
adq = result["adquirente"]  # KeyError: 'adquirente' no SQLite!
```

### Solução: Usar Acesso Dinâmico
```python
# ✅ CORRETO - Funciona em ambos
result = pd.read_sql("SELECT adquirente FROM vendas_processadas", engine)
col_name = result.columns[0]  # Pega o nome real da coluna
adq = result[col_name]  # Funciona em MySQL e SQLite
```

### Arquivos Corrigidos
- ✅ `modules/reports.py` - linha 536 (obter_adquirentes_distintos_processamento)
- ✅ `modules/reports.py` - linha 2203 (lançamentos de recebíveis)
- ✅ `modules/reports.py` - linha 2252 (total_perdas)
- ✅ `modules/reports.py` - linha 2595 (total_perdas_mdr/rr)
- ✅ `modules/reports.py` - linha 1867 (total_valor)
- ✅ `modules/reports.py` - linha 1937 (total_registros)
- ✅ `modules/reports.py` - linha 2014 (total_valor_recebivel/liquido)

---

## 🔧 7. Formatação de Datetime com strftime()

### Problema
Tentativa de usar `.strftime()` em valores que já são strings causa erro:
```
Invalid format specifier '%d/%m/%Y' for object of type 'str'
```

### Solução
```python
if isinstance(data_valor, str):
    data_formatada = data_valor  # Já é string
else:
    data_formatada = pd.to_datetime(data_valor).strftime("%d/%m/%Y")
```

### Arquivos Corrigidos
- ✅ `modules/reports.py` - linhas 2275-2303 (primeira_venda/ultima_venda)
- ✅ `modules/reports.py` - linhas 3309-3333 (mês de referência)

---

## 📝 Padrão Recomendado para Novas Queries

### 1. Sempre use a função helper `_is_sqlite(engine)`
```python
from conf.funcoesbd import _is_sqlite

if _is_sqlite(engine):
    # Código específico para SQLite
else:
    # Código específico para MySQL
```

### 2. Para acesso a colunas de resultados, use:
```python
# ✅ Método 1: Primeira coluna
result = pd.read_sql(query, engine)
valor = result.iloc[0][result.columns[0]]

# ✅ Método 2: Lista de colunas
cols = result.columns.tolist()
valor1 = result.iloc[0][cols[0]]
valor2 = result.iloc[0][cols[1]]

# ❌ EVITE:
valor = result.iloc[0]["nome_coluna"]  # Pode falhar no SQLite
```

### 3. Use aliases explícitos em queries SELECT
```python
# ✅ BOM - Alias explícito
"SELECT COUNT(*) as total FROM tabela"

# ❌ EVITE - Sem alias
"SELECT COUNT(*) FROM tabela"  # Nome da coluna pode variar
```

---

## 🧪 Checklist de Teste

Ao adicionar novas funcionalidades, teste em AMBOS os modos:

```bash
# Modo singleuser (SQLite)
python main.py --mode singleuser

# Modo deploy (MySQL)
python main.py --mode deploy
```

Verifique:
- [ ] Imports funcionam
- [ ] Cálculos executam sem erro
- [ ] Relatórios são gerados
- [ ] Gráficos são criados
- [ ] Dados são salvos corretamente

---

## 📊 Status Atual

| Componente | MySQL | SQLite | Status |
|------------|-------|--------|--------|
| Importação | ✅ | ✅ | OK |
| Cálculos | ✅ | ✅ | OK |
| Relatórios | ✅ | ✅ | OK |
| Gráficos | ✅ | ✅ | OK |
| Exportação | ✅ | ✅ | OK |

---

## 🔍 Ferramentas de Debug

Para investigar problemas de case-sensitivity:

```python
# Ver nomes exatos das colunas
result = pd.read_sql(query, engine)
print(f"Colunas retornadas: {result.columns.tolist()}")

# Ver tipo do banco
from conf.funcoesbd import _is_sqlite
print(f"É SQLite? {_is_sqlite(engine)}")
```

---

**Última atualização**: 13/11/2025
**Versão do Sistema**: 2.0 (Híbrido MySQL/SQLite)
