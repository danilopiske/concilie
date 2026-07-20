from typing import Any, Dict, List

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.schemas.analista import (
    AgregacaoBandeira,
    AgregacaoBandeiraForma,
    AgregacaoBandeiraFormaAno,
    AgregacaoFormaPagamento,
    AgregacaoFormaPagamentoAno,
    AgregacaoPeriodo,
    AgregacaoRecebivel,
    AnaliseDetalhadaItem,
    ConformidadeBandeiraForma,
    ConformidadePeriodoRow,
)


class AnalistaRepository:
    def __init__(self, db: Session):
        self.db = db
        self.dialect = db.get_bind().dialect.name  # 'sqlite' or 'mysql'

    def _get_year_sql(self, column: str) -> str:
        if self.dialect == 'sqlite':
            return f"strftime('%Y', {column})"
        else: # mysql
            return f"DATE_FORMAT({column}, '%Y')"

    def _get_period_sql(self, column: str, period_type: str) -> str:
        if self.dialect == 'sqlite':
            if period_type == 'mes':
                return f"strftime('%Y-%m', {column})"
            elif period_type == 'ano':
                return f"strftime('%Y', {column})"
            elif period_type == 'trimestre':
                return f"strftime('%Y', {column}) || '-Q' || ((CAST(strftime('%m', {column}) AS INTEGER) + 2) / 3)"
            elif period_type == 'semestre':
                return f"strftime('%Y', {column}) || '-S' || ((CAST(strftime('%m', {column}) AS INTEGER) - 1) / 6 + 1)"
        else: # mysql
            if period_type == 'mes':
                return f"DATE_FORMAT({column}, '%Y-%m')"
            elif period_type == 'ano':
                return f"DATE_FORMAT({column}, '%Y')"
            elif period_type == 'trimestre':
                return f"CONCAT(YEAR({column}), '-Q', QUARTER({column}))"
            elif period_type == 'semestre':
                 # Mysql doesn't have SEMESTER(), manual calc: IF(MONTH(col) <= 6, 1, 2)
                return f"CONCAT(YEAR({column}), '-S', IF(MONTH({column}) <= 6, 1, 2))"

        return "ERROR_PERIOD_TYPE"

    def get_bandeiras(self, processamento_id: str) -> List[AgregacaoBandeira]:
        sql = text("""
            SELECT
                Bandeira as bandeira,
                COUNT(*) as quantidade,
                SUM(Valor_da_venda) as valor_total,
                AVG(Valor_da_venda) as valor_medio,
                MIN(Valor_da_venda) as valor_min,
                MAX(Valor_da_venda) as valor_max,
                AVG(Taxas_Perc) as taxa_perc_media,
                SUM(Valor_descontado) as taxa_valor_total,
                SUM(Valor_RR) as vl_rr_total
            FROM vendas_processadas
            WHERE processamentoid = :pid
            GROUP BY Bandeira
            ORDER BY valor_total DESC
        """)

        results = self.db.execute(sql, {"pid": processamento_id}).fetchall()
        return [
            AgregacaoBandeira(
                bandeira=row.bandeira or "Desconhecido",
                quantidade=row.quantidade,
                valor_total=row.valor_total or 0.0,
                valor_medio=row.valor_medio or 0.0,
                valor_min=row.valor_min or 0.0,
                valor_max=row.valor_max or 0.0,
                taxa_perc_media=row.taxa_perc_media or 0.0,
                taxa_valor_total=row.taxa_valor_total or 0.0,
                vl_rr_total=float(row.vl_rr_total or 0.0)
            ) for row in results
        ]

    def get_formas_pagamento(self, processamento_id: str) -> List[AgregacaoFormaPagamento]:
        sql = text("""
            SELECT
                Forma_de_pagamento as forma_pagamento,
                COUNT(*) as quantidade,
                SUM(Valor_da_venda) as valor_total,
                AVG(Valor_da_venda) as valor_medio,
                MIN(Valor_da_venda) as valor_min,
                MAX(Valor_da_venda) as valor_max,
                AVG(Taxas_Perc) as taxa_perc_media,
                SUM(Valor_descontado) as taxa_valor_total,
                SUM(Valor_RR) as vl_rr_total
            FROM vendas_processadas
            WHERE processamentoid = :pid
            GROUP BY Forma_de_pagamento
            ORDER BY valor_total DESC
        """)

        results = self.db.execute(sql, {"pid": processamento_id}).fetchall()
        return [
            AgregacaoFormaPagamento(
                forma_pagamento=row.forma_pagamento or "Desconhecido",
                quantidade=row.quantidade,
                valor_total=row.valor_total or 0.0,
                valor_medio=row.valor_medio or 0.0,
                valor_min=row.valor_min or 0.0,
                valor_max=row.valor_max or 0.0,
                taxa_perc_media=row.taxa_perc_media or 0.0,
                taxa_valor_total=row.taxa_valor_total or 0.0,
                vl_rr_total=float(row.vl_rr_total or 0.0)
            ) for row in results
        ]

    def get_recebiveis(self, processamento_id: str) -> List[AgregacaoRecebivel]:
        # Check if table has records for this PID
        check = self.db.execute(text("SELECT COUNT(*) FROM recebiveis_processados WHERE processamentoid = :pid"), {"pid": processamento_id}).scalar()

        if check and check > 0:
            # Quote identifiers differently if needed, but ANSI quotes " usually work in both for column names
            # MySQL needs ANSI_QUOTES mode for ", otherwise `
            # For safety, let's use logic to strip quotes if MySQL or rely on sqlalchemy text() handling?
            # Actually standard types like "Tipo de Recebível" with spaces need quotes.
            # In MySQL, default is backtick `. SQLite uses ".

            col_tipo = '"Tipo de Recebível"'
            col_valor = '"Valor do Recebível"'

            if self.dialect != 'sqlite': # Assume MySQL default mode (no ANSI quotes)
                 col_tipo = '`Tipo de Recebível`'
                 col_valor = '`Valor do Recebível`'

            sql = text(f"""
                SELECT
                    {col_tipo} as tipo_recebivel,
                    COUNT(*) as quantidade,
                    SUM({col_valor}) as valor_total
                FROM recebiveis_processados
                WHERE processamentoid = :pid
                GROUP BY {col_tipo}
                ORDER BY valor_total DESC
            """)
            try:
                results = self.db.execute(sql, {"pid": processamento_id}).fetchall()
                return [
                    AgregacaoRecebivel(
                        tipo_recebivel=row.tipo_recebivel or "Indefinido",
                        quantidade=row.quantidade,
                        valor_total=row.valor_total or 0.0
                    ) for row in results
                ]
            except Exception:
                return []
        return []

    def get_periodos(self, processamento_id: str, tipo_periodo: str) -> List[AgregacaoPeriodo]:
        group_expr = self._get_period_sql("Data_da_venda", tipo_periodo)

        sql = text(f"""
            SELECT
                {group_expr} as periodo,
                COUNT(*) as quantidade,
                SUM(Valor_da_venda) as valor_total,
                AVG(Valor_da_venda) as valor_medio,
                MIN(Valor_da_venda) as valor_min,
                MAX(Valor_da_venda) as valor_max
            FROM vendas_processadas
            WHERE processamentoid = :pid AND Data_da_venda IS NOT NULL
            GROUP BY {group_expr}
            ORDER BY periodo
        """)

        results = self.db.execute(sql, {"pid": processamento_id}).fetchall()
        return [
            AgregacaoPeriodo(
                tipo_periodo=tipo_periodo,
                periodo=row.periodo,
                quantidade=row.quantidade,
                valor_total=row.valor_total or 0.0,
                valor_medio=row.valor_medio or 0.0,
                valor_min=row.valor_min or 0.0,
                valor_max=row.valor_max or 0.0
            ) for row in results
        ]

    def get_bandeira_forma(self, processamento_id: str) -> List[AgregacaoBandeiraForma]:
        sql = text("""
            SELECT
                Bandeira as bandeira,
                Forma_de_pagamento as forma_pagamento,
                COUNT(*) as quantidade,
                SUM(Valor_da_venda) as valor_total,
                AVG(Valor_da_venda) as valor_medio,
                AVG(Taxas_Perc) as taxa_perc_media,
                SUM(Valor_descontado) as taxa_valor_total,
                SUM(Valor_RR) as vl_rr_total
            FROM vendas_processadas
            WHERE processamentoid = :pid
            GROUP BY Bandeira, Forma_de_pagamento
            ORDER BY valor_total DESC
        """)
        results = self.db.execute(sql, {"pid": processamento_id}).fetchall()
        return [
            AgregacaoBandeiraForma(
                bandeira=row.bandeira or "Desconhecido",
                forma_pagamento=row.forma_pagamento or "Desconhecido",
                quantidade=row.quantidade,
                valor_total=row.valor_total or 0.0,
                valor_medio=row.valor_medio or 0.0,
                taxa_perc_media=row.taxa_perc_media or 0.0,
                taxa_valor_total=row.taxa_valor_total or 0.0,
                vl_rr_total=float(row.vl_rr_total or 0.0)
            ) for row in results
        ]

    def get_conformidade_bandeira_forma(self, processamento_id: str) -> List[ConformidadeBandeiraForma]:
        # Usa o calc_id mais recente gerado para este processamento
        sql = text("""
            SELECT
                vc.bandeira,
                vc.forma_pagamento,
                COUNT(*) as quantidade,
                SUM(vc.vl_venda) as faturamento,
                SUM(vc.vl_venda) - SUM(vc.desc_venda) as cielo_liquido,
                AVG(vc.tx_venda) as cielo_taxa_media,
                SUM(vc.desc_venda) as cielo_retido,
                SUM(vc.vl_liq_calc) as calc_liquido,
                AVG(vc.tx_calc) as calc_taxa_media,
                SUM(vc.desc_calc) as calc_retido,
                SUM(vc.perda) as nao_conformidade,
                SUM(vc.perda) / NULLIF(SUM(vc.vl_venda), 0) * 100 as nao_conformidade_perc,
                SUM(vc.perda_rr) as perda_rr
            FROM vendas_calculos vc
            INNER JOIN vendas_processadas vp ON vc.id_venda = vp.id
            WHERE vp.processamentoid = :pid
              AND vc.calc_id = (
                SELECT vc2.calc_id
                FROM vendas_calculos vc2
                INNER JOIN vendas_processadas vp2 ON vc2.id_venda = vp2.id
                WHERE vp2.processamentoid = :pid
                ORDER BY vc2.calc_data DESC
                LIMIT 1
              )
            GROUP BY vc.bandeira, vc.forma_pagamento
            ORDER BY vc.bandeira, vc.forma_pagamento
        """)
        results = self.db.execute(sql, {"pid": processamento_id}).fetchall()
        return [
            ConformidadeBandeiraForma(
                bandeira=row.bandeira or "Desconhecido",
                forma_pagamento=row.forma_pagamento or "Desconhecido",
                quantidade=row.quantidade,
                faturamento=float(row.faturamento or 0.0),
                cielo_liquido=float(row.cielo_liquido or 0.0),
                cielo_taxa_media=float(row.cielo_taxa_media or 0.0),
                cielo_retido=float(row.cielo_retido or 0.0),
                calc_liquido=float(row.calc_liquido or 0.0),
                calc_taxa_media=float(row.calc_taxa_media or 0.0),
                calc_retido=float(row.calc_retido or 0.0),
                nao_conformidade=float(row.nao_conformidade or 0.0),
                nao_conformidade_perc=float(row.nao_conformidade_perc or 0.0),
                perda_rr=float(row.perda_rr or 0.0),
            ) for row in results
        ]

    def get_conformidade_por_periodo(self, processamento_id: str, tipo: str) -> List[ConformidadePeriodoRow]:
        if tipo == "semestre":
            periodo_expr = "CONCAT(YEAR(vc.data_venda), '-S', IF(MONTH(vc.data_venda) <= 6, 1, 2))"
        elif tipo == "mes":
            periodo_expr = "DATE_FORMAT(vc.data_venda, '%Y-%m')"
        else:  # ano
            periodo_expr = "CAST(YEAR(vc.data_venda) AS CHAR)"

        sql = text(f"""
            SELECT
                {periodo_expr} as periodo,
                vc.bandeira,
                vc.forma_pagamento,
                COUNT(*) as quantidade,
                SUM(vc.vl_venda) as faturamento,
                AVG(vc.tx_venda) as cielo_taxa_media,
                SUM(vc.desc_venda) as cielo_retido,
                AVG(vc.tx_calc) as calc_taxa_media,
                SUM(vc.desc_calc) as calc_retido,
                SUM(vc.perda) as nao_conformidade,
                SUM(vc.perda) / NULLIF(SUM(vc.vl_venda), 0) * 100 as nao_conformidade_perc,
                SUM(vc.perda_rr) as perda_rr
            FROM vendas_calculos vc
            INNER JOIN vendas_processadas vp ON vc.id_venda = vp.id
            WHERE vp.processamentoid = :pid
              AND vc.calc_id = (
                SELECT vc2.calc_id
                FROM vendas_calculos vc2
                INNER JOIN vendas_processadas vp2 ON vc2.id_venda = vp2.id
                WHERE vp2.processamentoid = :pid
                ORDER BY vc2.calc_data DESC
                LIMIT 1
              )
              AND vc.data_venda IS NOT NULL
            GROUP BY periodo, vc.bandeira, vc.forma_pagamento
            ORDER BY periodo, vc.bandeira, vc.forma_pagamento
        """)
        results = self.db.execute(sql, {"pid": processamento_id}).fetchall()
        return [
            ConformidadePeriodoRow(
                periodo=str(row.periodo or ""),
                bandeira=row.bandeira or "Desconhecido",
                forma_pagamento=row.forma_pagamento or "Desconhecido",
                quantidade=row.quantidade,
                faturamento=float(row.faturamento or 0.0),
                cielo_taxa_media=float(row.cielo_taxa_media or 0.0),
                cielo_retido=float(row.cielo_retido or 0.0),
                calc_taxa_media=float(row.calc_taxa_media or 0.0),
                calc_retido=float(row.calc_retido or 0.0),
                nao_conformidade=float(row.nao_conformidade or 0.0),
                nao_conformidade_perc=float(row.nao_conformidade_perc or 0.0),
                perda_rr=float(row.perda_rr or 0.0),
            ) for row in results
        ]

    # ── Filtradas ─────────────────────────────────────────────────────────────

    def get_bandeiras_filtradas(self, processamento_id: str) -> List[AgregacaoBandeira]:
        sql = text("""
            SELECT
                Bandeira as bandeira,
                COUNT(*) as quantidade,
                SUM(Valor_da_venda) as valor_total,
                AVG(Valor_da_venda) as valor_medio,
                MIN(Valor_da_venda) as valor_min,
                MAX(Valor_da_venda) as valor_max
            FROM vendas_filtradas
            WHERE processamentoid = :pid
            GROUP BY Bandeira
            ORDER BY valor_total DESC
        """)
        results = self.db.execute(sql, {"pid": processamento_id}).fetchall()
        return [
            AgregacaoBandeira(
                bandeira=row.bandeira or "Desconhecido",
                quantidade=row.quantidade,
                valor_total=row.valor_total or 0.0,
                valor_medio=row.valor_medio or 0.0,
                valor_min=row.valor_min or 0.0,
                valor_max=row.valor_max or 0.0,
            ) for row in results
        ]

    def get_formas_pagamento_filtradas(self, processamento_id: str) -> List[AgregacaoFormaPagamento]:
        sql = text("""
            SELECT
                Forma_de_pagamento as forma_pagamento,
                COUNT(*) as quantidade,
                SUM(Valor_da_venda) as valor_total,
                AVG(Valor_da_venda) as valor_medio,
                MIN(Valor_da_venda) as valor_min,
                MAX(Valor_da_venda) as valor_max
            FROM vendas_filtradas
            WHERE processamentoid = :pid
            GROUP BY Forma_de_pagamento
            ORDER BY valor_total DESC
        """)
        results = self.db.execute(sql, {"pid": processamento_id}).fetchall()
        return [
            AgregacaoFormaPagamento(
                forma_pagamento=row.forma_pagamento or "Desconhecido",
                quantidade=row.quantidade,
                valor_total=row.valor_total or 0.0,
                valor_medio=row.valor_medio or 0.0,
                valor_min=row.valor_min or 0.0,
                valor_max=row.valor_max or 0.0,
            ) for row in results
        ]

    def get_recebiveis_filtrados(self, processamento_id: str) -> List[AgregacaoRecebivel]:
        check = self.db.execute(
            text("SELECT COUNT(*) FROM recebiveis_filtrados WHERE processamentoid = :pid"),
            {"pid": processamento_id}
        ).scalar()
        if not check or check == 0:
            return []
        sql = text("""
            SELECT
                lancamento as tipo_recebivel,
                COUNT(*) as quantidade,
                SUM(valor_recebivel) as valor_total
            FROM recebiveis_filtrados
            WHERE processamentoid = :pid
            GROUP BY lancamento
            ORDER BY valor_total DESC
        """)
        try:
            results = self.db.execute(sql, {"pid": processamento_id}).fetchall()
            return [
                AgregacaoRecebivel(
                    tipo_recebivel=row.tipo_recebivel or "Indefinido",
                    quantidade=row.quantidade,
                    valor_total=row.valor_total or 0.0
                ) for row in results
            ]
        except Exception:
            return []

    def get_periodos_filtradas(self, processamento_id: str, tipo_periodo: str) -> List[AgregacaoPeriodo]:
        group_expr = self._get_period_sql("data_da_venda", tipo_periodo)
        sql = text(f"""
            SELECT
                {group_expr} as periodo,
                COUNT(*) as quantidade,
                SUM(Valor_da_venda) as valor_total,
                AVG(Valor_da_venda) as valor_medio,
                MIN(Valor_da_venda) as valor_min,
                MAX(Valor_da_venda) as valor_max
            FROM vendas_filtradas
            WHERE processamentoid = :pid AND data_da_venda IS NOT NULL
            GROUP BY {group_expr}
            ORDER BY periodo
        """)
        results = self.db.execute(sql, {"pid": processamento_id}).fetchall()
        return [
            AgregacaoPeriodo(
                tipo_periodo=tipo_periodo,
                periodo=row.periodo,
                quantidade=row.quantidade,
                valor_total=row.valor_total or 0.0,
                valor_medio=row.valor_medio or 0.0,
                valor_min=row.valor_min or 0.0,
                valor_max=row.valor_max or 0.0,
            ) for row in results
        ]

    def get_bandeira_forma_filtrada(self, processamento_id: str) -> List[AgregacaoBandeiraForma]:
        sql = text("""
            SELECT
                Bandeira as bandeira,
                Forma_de_pagamento as forma_pagamento,
                COUNT(*) as quantidade,
                SUM(Valor_da_venda) as valor_total,
                AVG(Valor_da_venda) as valor_medio
            FROM vendas_filtradas
            WHERE processamentoid = :pid
            GROUP BY Bandeira, Forma_de_pagamento
            ORDER BY valor_total DESC
        """)
        results = self.db.execute(sql, {"pid": processamento_id}).fetchall()
        return [
            AgregacaoBandeiraForma(
                bandeira=row.bandeira or "Desconhecido",
                forma_pagamento=row.forma_pagamento or "Desconhecido",
                quantidade=row.quantidade,
                valor_total=row.valor_total or 0.0,
                valor_medio=row.valor_medio or 0.0,
            ) for row in results
        ]

    def get_bandeira_forma_por_ano_filtrada(self, processamento_id: str) -> List[AgregacaoBandeiraFormaAno]:
        year_expr = self._get_year_sql("data_da_venda")
        sql = text(f"""
            SELECT
                {year_expr} as ano,
                Bandeira as bandeira,
                Forma_de_pagamento as forma_pagamento,
                COUNT(*) as quantidade,
                SUM(Valor_da_venda) as valor_total,
                AVG(Valor_da_venda) as valor_medio
            FROM vendas_filtradas
            WHERE processamentoid = :pid AND data_da_venda IS NOT NULL
            GROUP BY {year_expr}, Bandeira, Forma_de_pagamento
            ORDER BY ano, valor_total DESC
        """)
        results = self.db.execute(sql, {"pid": processamento_id}).fetchall()
        return [
            AgregacaoBandeiraFormaAno(
                ano=row.ano,
                bandeira=row.bandeira or "Desconhecido",
                forma_pagamento=row.forma_pagamento or "Desconhecido",
                quantidade=row.quantidade,
                valor_total=row.valor_total or 0.0,
                valor_medio=row.valor_medio or 0.0,
            ) for row in results
        ]

    def get_formas_por_ano_filtradas(self, processamento_id: str) -> List[AgregacaoFormaPagamentoAno]:
        year_expr = self._get_year_sql("data_da_venda")
        sql = text(f"""
            SELECT
                {year_expr} as ano,
                Forma_de_pagamento as forma_pagamento,
                COUNT(*) as quantidade,
                SUM(Valor_da_venda) as valor_total,
                AVG(Valor_da_venda) as valor_medio
            FROM vendas_filtradas
            WHERE processamentoid = :pid AND data_da_venda IS NOT NULL
            GROUP BY {year_expr}, Forma_de_pagamento
            ORDER BY ano, valor_total DESC
        """)
        results = self.db.execute(sql, {"pid": processamento_id}).fetchall()
        return [
            AgregacaoFormaPagamentoAno(
                ano=row.ano,
                forma_pagamento=row.forma_pagamento or "Desconhecido",
                quantidade=row.quantidade,
                valor_total=row.valor_total or 0.0,
                valor_medio=row.valor_medio or 0.0,
            ) for row in results
        ]

    def get_bandeira_forma_por_ano(self, processamento_id: str) -> List[AgregacaoBandeiraFormaAno]:
        year_expr = self._get_year_sql("Data_da_venda")

        sql = text(f"""
            SELECT
                {year_expr} as ano,
                Bandeira as bandeira,
                Forma_de_pagamento as forma_pagamento,
                COUNT(*) as quantidade,
                SUM(Valor_da_venda) as valor_total,
                AVG(Valor_da_venda) as valor_medio,
                MIN(Taxas_Perc) as taxa_perc_minima,
                MAX(Taxas_Perc) as taxa_perc_maxima
            FROM vendas_processadas
            WHERE processamentoid = :pid AND Data_da_venda IS NOT NULL
            GROUP BY {year_expr}, Bandeira, Forma_de_pagamento
            ORDER BY ano, valor_total DESC
        """)

        results = self.db.execute(sql, {"pid": processamento_id}).fetchall()
        return [
            AgregacaoBandeiraFormaAno(
                ano=row.ano,
                bandeira=row.bandeira or "Desconhecido",
                forma_pagamento=row.forma_pagamento or "Desconhecido",
                quantidade=row.quantidade,
                valor_total=row.valor_total or 0.0,
                valor_medio=row.valor_medio or 0.0,
                taxa_perc_minima=row.taxa_perc_minima or 0.0,
                taxa_perc_maxima=row.taxa_perc_maxima or 0.0
            ) for row in results
        ]

    def get_formas_por_ano(self, processamento_id: str) -> List[AgregacaoFormaPagamentoAno]:
        year_expr = self._get_year_sql("Data_da_venda")

        sql = text(f"""
            SELECT
                {year_expr} as ano,
                Forma_de_pagamento as forma_pagamento,
                COUNT(*) as quantidade,
                SUM(Valor_da_venda) as valor_total,
                AVG(Valor_da_venda) as valor_medio,
                MIN(Taxas_Perc) as taxa_perc_minima,
                MAX(Taxas_Perc) as taxa_perc_maxima
            FROM vendas_processadas
            WHERE processamentoid = :pid AND Data_da_venda IS NOT NULL
            GROUP BY {year_expr}, Forma_de_pagamento
            ORDER BY ano, valor_total DESC
        """)

        results = self.db.execute(sql, {"pid": processamento_id}).fetchall()
        return [
            AgregacaoFormaPagamentoAno(
                ano=row.ano,
                forma_pagamento=row.forma_pagamento or "Desconhecido",
                quantidade=row.quantidade,
                valor_total=row.valor_total or 0.0,
                valor_medio=row.valor_medio or 0.0,
                taxa_perc_minima=row.taxa_perc_minima or 0.0,
                taxa_perc_maxima=row.taxa_perc_maxima or 0.0
            ) for row in results
        ]
