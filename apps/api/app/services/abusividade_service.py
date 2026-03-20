from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import polars as pl
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.models.vendas_calculos import VendasCalculos


class AbusividadeService:
    def __init__(self, db: Session):
        self.db = db

    def analisar_processamento(self, processamento_id: str, agrupamento: str = 'hierarquico', tolerancia: float = 0.0) -> List[Dict[str, Any]]:
        """
        Analisa um processamento específico em busca de variações de taxa usando Polars para alta performance.
        """
        if agrupamento == 'hierarquico':
            return self._analisar_hierarquia(processamento_id, tolerancia=tolerancia)

        return self._detectar_variacoes_polars(processamento_id=processamento_id, agrupamento=agrupamento, tolerancia=tolerancia)

    def _analisar_hierarquia(self, processamento_id: str, tolerancia: float = 0.0) -> List[Dict[str, Any]]:
        """
        Analisa a hierarquia (dia, 3dias, semana, mes) de uma vez só usando Polars.
        """
        niveis = ['dia', '3dias', 'semana', 'mes']
        todos_resultados = []
        ids_processados = set()

        for nivel in niveis:
            resultados = self._detectar_variacoes_polars(processamento_id=processamento_id, agrupamento=nivel, tolerancia=tolerancia)

            for item in resultados:
                if item['id'] not in ids_processados:
                    ids_processados.add(item['id'])
                    todos_resultados.append(item)

        todos_resultados.sort(key=lambda x: x['data_venda'] or datetime.min)
        return todos_resultados

    def _detectar_variacoes_polars(
        self,
        processamento_id: Optional[str] = None,
        cliente_id: Optional[int] = None,
        ec_id: Optional[str] = None,
        data_ini: Optional[datetime] = None,
        data_fim: Optional[datetime] = None,
        agrupamento: str = 'periodo_total',
        tolerancia: float = 0.0
    ) -> List[Dict[str, Any]]:
        """
        Núcleo Otimizado com Polars:
        1. Carrega dados do banco via query SQL direta (mais rápido que ORM).
        2. Processamento vetorizado para detectar variações de taxa.
        """
        engine = self.db.get_bind()

        # 1. Construir query SQL eficiente
        sql = "SELECT id, calc_id, data_venda, ec_id, bandeira, forma_pagamento, tx_venda, vl_venda, cod_autorizacao, nsu FROM vendas_calculos WHERE 1=1"
        params = {}

        if processamento_id:
            sql += " AND calc_id = :calc_id"
            params["calc_id"] = str(processamento_id)
        if ec_id:
            sql += " AND ec_id = :ec_id"
            params["ec_id"] = ec_id
        if data_ini:
            sql += " AND data_venda >= :data_ini"
            params["data_ini"] = data_ini
        if data_fim:
            sql += " AND data_venda <= :data_fim"
            params["data_fim"] = data_fim

        # 2. Carregar para Polars
        try:
            lf = pl.read_database(sql, connection=engine, partition_column=None, row_picker=None, params=params).lazy()

            # Se vazio, retorna logo
            if lf.collect().is_empty():
                return []
        except Exception as e:
            print(f"Error loading data with Polars: {e}")
            # Fallback for empty results or connection issues
            return []

        # 3. Preparar Chave de Agrupamento
        lf = lf.with_columns([
            pl.col("data_venda").cast(pl.Datetime).alias("dt"),
            pl.col("tx_venda").cast(pl.Float64).fill_null(0.0).alias("taxa")
        ])

        # Definir a coluna de agrupamento temporal
        if agrupamento == 'dia':
            lf = lf.with_columns(pl.col("dt").dt.strftime("%Y-%m-%d").alias("periodo"))
        elif agrupamento == '3dias':
            # toordinal // 3 equivalent in Polars: cast to date, then to integer, then integer divide
            # Actually simpler: pl.col("dt").dt.truncate("3d")
            lf = lf.with_columns(pl.col("dt").dt.truncate("3d").dt.strftime("%Y-%m-%d").alias("periodo"))
        elif agrupamento == 'semana':
            lf = lf.with_columns(pl.col("dt").dt.truncate("1w").dt.strftime("%Y-W%V").alias("periodo"))
        elif agrupamento == 'mes':
            lf = lf.with_columns(pl.col("dt").dt.strftime("%Y-%m").alias("periodo"))
        else:
            lf = lf.with_columns(pl.lit("TOTAL").alias("periodo"))

        # Chave base: Bandeira + Forma Pagamento + Periodo
        lf = lf.with_columns(
            (pl.col("bandeira") + "|" + pl.col("forma_pagamento") + "|" + pl.col("periodo")).alias("chave_agrupamento")
        )

        # 4. Detectar Variações (Agrupamento e Filtro Vetorizado)
        # Encontrar chaves que possuem mais de uma taxa distinta
        variacoes_videntes = (
            lf.group_by("chave_agrupamento")
            .agg([
                pl.col("taxa").n_unique().alias("n_taxas"),
                pl.col("taxa").min().alias("min_taxa"),
                pl.col("taxa").max().alias("max_taxa")
            ])
            .filter(pl.col("n_taxas") > 1)
        )

        # Aplicar tolerância se necessário
        if tolerancia > 0.0:
            variacoes_videntes = variacoes_videntes.filter((pl.col("max_taxa") - pl.col("min_taxa")) > tolerancia)

        # 5. Join de volta para pegar o detalhe das transações que estão nessas chaves
        chaves_com_problema = variacoes_videntes.select("chave_agrupamento")

        resultado_final = (
            lf.join(chaves_com_problema, on="chave_agrupamento", how="inner")
            .sort("dt")
            .collect()
        )

        # 6. Converter para lista de dicionários no formato esperado pela UI/Relatório
        # Otimizado: Convertemos o DF inteiro para dicts de uma vez
        rows = []
        for r in resultado_final.to_dicts():
            rows.append({
                "id": r["id"],
                "data_venda": r["dt"],
                "cod_autorizacao": r["cod_autorizacao"] or r["nsu"] or "N/A",
                "horario": r["dt"].strftime("%H:%M:%S") if r["dt"] else "--",
                "valor_venda": float(r["vl_venda"]) if r["vl_venda"] else 0.0,
                "taxa_aplicada": float(r["taxa"]),
                "numero_maquina": r["ec_id"],
                "bandeira": r["bandeira"],
                "forma_pagamento": r["forma_pagamento"],
                "chave_agrupamento": r["chave_agrupamento"]
            })

        return rows
