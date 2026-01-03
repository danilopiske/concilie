#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script para encontrar chamadas de funções SQL que precisam ser atualizadas
para incluir o parâmetro 'engine'.

Uso:
    python find_updates_needed.py
"""

import os
import re
from pathlib import Path

# Funções que agora requerem engine como primeiro parâmetro
FUNCTIONS = [
    "_normalize_text_compare",
    "_date_format_sql",
    "_concat_sql",
    "_insert_ignore_sql",
    "_year_sql",
    "_month_sql",
    "_quarter_sql",
    "_semester_sql",
    "_get_table_columns",
    "_upsert_sql",
]


def find_in_file(filepath):
    """Busca chamadas antigas em um arquivo."""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
    except Exception as e:
        print(f"  ⚠️  Erro ao ler {filepath}: {e}")
        return []

    found = []
    lines = content.split("\n")

    for func in FUNCTIONS:
        # Padrões para encontrar chamadas
        patterns = [
            # Padrão 1: funcao( sem 'engine' logo após
            rf"{func}\s*\(\s*(?!engine)",
            # Padrão 2: Verifica se tem engine, mas considera chamadas válidas
            # (este padrão captura false positives, então filtramos depois)
        ]

        for i, line in enumerate(lines, 1):
            for pattern in patterns:
                if re.search(pattern, line):
                    # Verifica se não é uma definição da função
                    if f"def {func}" not in line:
                        # Verifica se não já tem engine
                        if (
                            f"{func}(engine" not in line
                            and f"{func}( engine" not in line
                        ):
                            found.append(
                                {
                                    "function": func,
                                    "line_num": i,
                                    "line_content": line.strip(),
                                }
                            )

    return found


def scan_directory(directory):
    """Escaneia diretório procurando arquivos Python."""
    results = {}

    directory_path = Path(directory)
    if not directory_path.exists():
        return results

    for filepath in directory_path.rglob("*.py"):
        # Ignora __pycache__, .venv, etc
        if any(
            part.startswith(".") or part == "__pycache__" for part in filepath.parts
        ):
            continue

        # Ignora conf/funcoesbd.py (onde as funções estão definidas)
        if "funcoesbd.py" in str(filepath):
            continue

        found = find_in_file(filepath)

        if found:
            results[str(filepath)] = found

    return results


def main():
    """Função principal."""
    print("=" * 80)
    print("🔍 BUSCANDO CHAMADAS QUE PRECISAM DE ATUALIZAÇÃO")
    print("=" * 80)
    print()
    print("Procurando por chamadas de funções SQL que agora requerem 'engine'...")
    print()

    # Escaneia modules/ e proc/
    all_results = {}
    directories = ["modules", "proc"]

    for directory in directories:
        if os.path.exists(directory):
            print(f"📁 Escaneando {directory}/...")
            results = scan_directory(directory)
            all_results.update(results)

    print()
    print("=" * 80)

    if not all_results:
        print("✅ NENHUMA CHAMADA ANTIGA ENCONTRADA!")
        print()
        print("Seu código já está atualizado ou não usa essas funções.")
    else:
        total_issues = sum(len(v) for v in all_results.values())
        print(f"⚠️  ENCONTRADAS {total_issues} CHAMADAS PARA ATUALIZAR")
        print()

        for filepath, findings in sorted(all_results.items()):
            print()
            print(f"📄 {filepath}")
            print("-" * 80)

            # Agrupa por função
            by_function = {}
            for finding in findings:
                func = finding["function"]
                if func not in by_function:
                    by_function[func] = []
                by_function[func].append(finding)

            for func, items in sorted(by_function.items()):
                print(f"\n  🔧 {func}() - {len(items)} ocorrência(s)")
                for item in items:
                    print(
                        f"     Linha {item['line_num']:4d}: {item['line_content'][:70]}"
                    )

        print()
        print("=" * 80)
        print("💡 COMO CORRIGIR:")
        print("=" * 80)
        print()
        print("1. Adicione 'engine' como PRIMEIRO parâmetro em cada chamada:")
        print()
        print("   ❌ ANTES:")
        print("      _year_sql('data_venda')")
        print()
        print("   ✅ DEPOIS:")
        print("      _year_sql(engine, 'data_venda')")
        print()
        print("2. Certifique-se de que a função que faz a chamada recebe 'engine':")
        print()
        print("   def minha_funcao(engine):  # ← engine aqui")
        print("       ano = _year_sql(engine, 'data')  # ← e aqui")
        print()
        print("3. Consulte MIGRATION_GUIDE.md para exemplos detalhados")
        print()

    print("=" * 80)
    print()


if __name__ == "__main__":
    main()
