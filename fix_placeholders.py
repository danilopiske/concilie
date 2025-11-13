"""
Script para converter todos os placeholders %s para _convert_placeholders()
em reports.py
"""

import re

file_path = r"d:\Financial Checker base\Financial_P\modules\reports.py"

# Ler o arquivo
with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

# Padrões de queries que precisam de conversão
# Queries SQL que contêm %s e são seguidas por pd.read_sql
patterns_to_fix = [
    # Padrão: sql = "SELECT ... %s"
    # seguido por pd.read_sql(sql, ...)
    (
        r'(\s+)(\w+_sql\s*=\s*"""[^"]*%s[^"]*""")\s*\n(\s+)(df_\w+|resultado|total_valor_df|df_verificacao|df_demonstrativo|df_perdas|df_recebiveis|df_ecs|df_calcs|df_recebiveis_mat)\s*=\s*pd\.read_sql\(\s*(\w+_sql)',
        r"\1\2\n\3\5 = _convert_placeholders(engine, \5)\n\3\4 = pd.read_sql(\5",
    ),
    (
        r'(\s+)(\w+_sql\s*=\s*"[^"]*%s[^"]*")\s*\n(\s+)(df_\w+|resultado|total_valor_df|df_verificacao|df_demonstrativo|df_perdas|df_recebiveis|df_ecs|df_calcs|df_recebiveis_mat)\s*=\s*pd\.read_sql\(\s*(\w+_sql)',
        r"\1\2\n\3\5 = _convert_placeholders(engine, \5)\n\3\4 = pd.read_sql(\5",
    ),
    # Padrão inline: pd.read_sql("SELECT ... %s", engine, ...)
    (
        r'pd\.read_sql\(\s*"([^"]*%s[^"]*)",\s*engine',
        r'pd.read_sql(_convert_placeholders(engine, "\1"), engine',
    ),
    (
        r"pd\.read_sql\(\s*'([^']*%s[^']*)',\s*engine",
        r"pd.read_sql(_convert_placeholders(engine, '\1'), engine",
    ),
]

# Contar occorrências antes
count_before = content.count("%s")
print(f"Total de %s antes: {count_before}")
print(f"Total de _convert_placeholders antes: {content.count('_convert_placeholders')}")

# Aplicar correções simples e seguras
# Corrigir queries individuais que estão claramente definidas antes de pd.read_sql

queries_to_fix = [
    (
        r'(sql\s*=\s*"SELECT \* FROM recebiveis_processados WHERE processamentoid = %s")',
        r"\1\n    sql = _convert_placeholders(engine, sql)",
    ),
    (
        r'(sql_recebiveis\s*=\s*"""[^"]*processamentoid = %s[^"]*""")',
        r"\1\n        sql_recebiveis = _convert_placeholders(engine, sql_recebiveis)",
    ),
    (
        r'(sql_total\s*=\s*"""[^"]*processamentoid = %s[^"]*""")',
        r"\1\n        sql_total = _convert_placeholders(engine, sql_total)",
    ),
    (
        r'(verificacao_sql\s*=\s*"""[^"]*processamentoid = %s[^"]*""")',
        r"\1\n        verificacao_sql = _convert_placeholders(engine, verificacao_sql)",
    ),
    (
        r'(recebiveis_sql\s*=\s*"SELECT DISTINCT lancamento FROM recebiveis_processados WHERE processamentoid = %s[^"]*")',
        r"\1\n        recebiveis_sql = _convert_placeholders(engine, recebiveis_sql)",
    ),
    (
        r'(perdas_sql\s*=\s*"""[^"]*calc_id = %s[^"]*""")',
        r"\1\n                perdas_sql = _convert_placeholders(engine, perdas_sql)",
    ),
    (
        r'(sql_perdas\s*=\s*"""[^"]*calc_id = %s[^"]*""")',
        r"\1\n        sql_perdas = _convert_placeholders(engine, sql_perdas)",
    ),
    (
        r'(join_sql\s*=\s*"""[^"]*calc_id = %s[^"]*""")\s*\n(\s+)if adquirente:',
        r"\1\n\2if adquirente:",
    ),
]

new_content = content
for pattern, replacement in queries_to_fix:
    new_content = re.sub(pattern, replacement, new_content)

# Contar ocorrências depois
count_after = new_content.count("%s")
conversoes = count_before - count_after
print(f"\nTotal de %s depois: {count_after}")
print(
    f"Total de _convert_placeholders depois: {new_content.count('_convert_placeholders')}"
)
print(f"Conversões realizadas: {conversoes}")

# Salvar o arquivo
if conversoes > 0:
    backup_path = file_path + ".backup"
    with open(backup_path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"\nBackup salvo em: {backup_path}")

    with open(file_path, "w", encoding="utf-8") as f:
        f.write(new_content)
    print(f"Arquivo atualizado: {file_path}")
else:
    print("\nNenhuma conversão necessária.")
