from typing import List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.schemas.analista import (
    AgregacaoBandeira,
    AgregacaoFormaPagamento,
    AgregacaoPeriodo,
    AgregacaoRecebivel,
    AgregacaoFormaPagamentoAno,
    AnaliseDetalhadaItem
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
                SUM(Valor_descontado) as taxa_valor_total
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
                taxa_valor_total=row.taxa_valor_total or 0.0
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
                SUM(Valor_descontado) as taxa_valor_total
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
                taxa_valor_total=row.taxa_valor_total or 0.0
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
