import statistics
import time
from datetime import date, datetime

from dateutil.relativedelta import relativedelta
from sqlalchemy import func, text
from sqlalchemy.orm import Session

from app.models.vendas_calculos import VendasCalculos
from app.schemas.calculo import (
    AnalisePeriodosResponse,
    CalculoPreviewRequest,
    CalculoRequest,
    CalculoStats,
    PeriodoAnalise,
)


class CalculoRepository:
    def __init__(self, db: Session):
        self.db = db
        self.dialect = db.get_bind().dialect.name

    def _get_period_formula(self, alias="vp", col_name="Data_da_venda"):
        """Returns DBMS-specific formula for 'Year-01-01'"""
        if self.dialect == 'sqlite':
            return f"strftime('%Y', {alias}.{col_name}) || '-01-01'"
        else:
            return f"CONCAT(YEAR({alias}.{col_name}), '-01-01')"

    def preview_calculo(self, req: CalculoPreviewRequest) -> CalculoStats:
        # Check if processamento exists and has sales
        sql = text("""
            SELECT COUNT(*) as total, SUM(Valor_da_venda) as valor_total, AVG(Valor_da_venda) as valor_medio,
                   MIN(Taxas_Perc) as min_taxa, MAX(Taxas_Perc) as max_taxa, AVG(Taxas_Perc) as avg_taxa,
                   SUM(CASE WHEN Taxas_RR > 0 THEN 1 ELSE 0 END) as taxas_rr_count
            FROM vendas_processadas
            WHERE processamentoid = :pid
        """)
        result = self.db.execute(sql, {"pid": req.processamento_id}).fetchone()

        if not result or result[0] == 0:
            return CalculoStats(total_vendas=0, valor_total=0, valor_medio=0, min_taxa_orig=0, max_taxa_orig=0, media_taxa_orig=0)

        # Basic Stats
        total_vendas = result[0]
        vendas_com_cad = 0

        # Simulate Taxa CAD count if enabled
        if req.usar_taxa_cad:
            # This is complex to estimate perfectly without full join, getting approx count via logic
            # For brevity in preview, we might just return 0 or implement a simplified count query
            # Implementing a simplified count:
             sql_cad = text("""
                SELECT COUNT(*)
                FROM vendas_processadas vp
                JOIN taxas t ON t.ec = vp.ec_id
                    AND LOWER(t.bandeira) = LOWER(vp.Bandeira)
                    AND LOWER(t.forma_pagamento) = LOWER(vp.Forma_de_pagamento)
                    AND vp.Data_da_venda BETWEEN t.data_ini AND t.data_fim
                WHERE vp.processamentoid = :pid
            """)
             vendas_com_cad = self.db.execute(sql_cad, {"pid": req.processamento_id}).scalar() or 0

        return CalculoStats(
            total_vendas=total_vendas,
            valor_total=result[1] or 0,
            valor_medio=result[2] or 0,
            min_taxa_orig=result[3] or 0,
            max_taxa_orig=result[4] or 0,
            media_taxa_orig=result[5] or 0,
            vendas_com_cad=vendas_com_cad,
            vendas_com_log=total_vendas - vendas_com_cad if req.usar_taxa_cad else total_vendas,
            taxas_rr_count=result[6] or 0
        )

    def processar_calculo(self, req: CalculoRequest, usuario_logado: str = "sistema"):
        # 0. Generate Unique ID: {ec_id}_{tipo_sem_log}_{timestamp}
        # First, find the ec_id for this processamento
        ec_sql = text("SELECT ec_id FROM vendas_processadas WHERE processamentoid = :pid LIMIT 1")
        ec_res = self.db.execute(ec_sql, {"pid": req.processamento_id}).fetchone()
        ec_id = str(ec_res[0]) if ec_res else "unknown"

        tipo_clean = req.tipo_taxa.replace("log_", "")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        custom_id = f"{ec_id}_{tipo_clean}_{timestamp}"

        # 1. Clear previous calculation IF substituir is True
        if req.substituir:
            # We delete calculations of the same TYPE for this PROCESSAMENTO
            # We reference by the sales that belong to this processamento_id
            sql_del = text("""
                DELETE FROM vendas_calculos
                WHERE id_venda IN (SELECT id FROM vendas_processadas WHERE processamentoid = :pid)
                AND calc_tipo = :tipo
            """)
            self.db.execute(sql_del, {"pid": req.processamento_id, "tipo": req.tipo_taxa})
            self.db.commit()

        # 2. Return the generated ID — ReconciliationCore handles the actual INSERT
        return custom_id

        # 3. Apply Calculations (UPDATEs)

        # 3A. Taxa de Log (Minimum Rate in Period)
        # Logic: Find min(Taxas_Perc) for same EC, Bandeira, FormaPagamento in period
        # We need to port `_convert_min_tx_update_for_sqlite` logic essentially

        # 3A. Taxa de Log (Minimum Rate in Period)
        # Using UPDATE JOIN which is compatible with MySQL

        period_formula_vp = self._get_period_formula("vp", col_name="Data_da_venda")
        period_formula_vc = self._get_period_formula("vc", col_name="data_venda")

        # IMPORTANT: We join on lower case strings to match Python/SQLite logic
        # But in MySQL default collation is case insensitive anyway. Explicit lower is safer.

        update_sql = f"""
            UPDATE vendas_calculos vc
            JOIN (
                SELECT
                    vp.ec_id,
                    vp.Bandeira as bandeira,
                    vp.Forma_de_pagamento as forma_pagamento,
                    {period_formula_vp} as periodo_ini,
                    MIN(vp.Taxas_Perc) as min_tx_venda
                FROM vendas_processadas vp
                WHERE vp.processamentoid = :pid AND vp.Taxas_Perc > 0
                GROUP BY vp.ec_id, vp.Bandeira, vp.Forma_de_pagamento, {period_formula_vp}
            ) min_table ON
                vc.ec_id = min_table.ec_id
                AND vc.bandeira = min_table.bandeira
                AND vc.forma_pagamento = min_table.forma_pagamento
                AND {period_formula_vc} = min_table.periodo_ini
            SET vc.tx_calc = min_table.min_tx_venda
            WHERE vc.calc_id = :calc_id AND vc.calc_tipo = :calc_tipo
        """

        # Adjust for SQLite if needed (SQLite doesn't support UPDATE JOIN directly in standard SQL standard,
        # but supports FROM clause in some versions or requires the scalar subquery approach).
        if self.dialect == 'sqlite':
            # Fallback to the scalar subquery approach for SQLite which we know works there
             period_formula = self._get_period_formula("vp") # reuse helper
             # Note: SQLite CTE support in UPDATE is limited in some python libs/driver versions,
             # but scalar subquery in SET is standard.
             update_sql = f"""
                 UPDATE vendas_calculos
                 SET tx_calc = (
                    SELECT MIN(vp.Taxas_Perc)
                    FROM vendas_processadas vp
                    WHERE vp.processamentoid = :pid
                      AND vp.Taxas_Perc > 0
                      AND vp.ec_id = vendas_calculos.ec_id
                      AND LOWER(vp.Bandeira) = LOWER(vendas_calculos.bandeira)
                      AND LOWER(vp.Forma_de_pagamento) = LOWER(vendas_calculos.forma_pagamento)
                      AND {self._get_period_formula("vp", col_name="Data_da_venda")} = {self._get_period_formula("vendas_calculos", col_name="data_venda")}
                 )
                 WHERE calc_id = :calc_id AND calc_tipo = :calc_tipo
             """

        self.db.execute(text(update_sql), {"pid": req.processamento_id, "calc_id": req.processamento_id, "calc_tipo": req.tipo_taxa})

        # 3B. Taxa CAD (If enabled)
        if req.usar_taxa_cad:
            # Logic: Update tx_calc from TAXAS table where matches
            # SQLite: UPDATE using subquery
            sql_cad = text("""
                UPDATE vendas_calculos
                SET tx_calc = (
                    SELECT t.taxa
                    FROM taxas t
                    WHERE t.ec = vendas_calculos.ec_id
                    AND LOWER(t.bandeira) = LOWER(vendas_calculos.bandeira)
                    AND LOWER(t.forma_pagamento) = LOWER(vendas_calculos.forma_pagamento)
                    AND vendas_calculos.calc_data BETWEEN t.data_ini AND t.data_fim
                    LIMIT 1
                )
                WHERE calc_id = :calc_id
                  AND calc_tipo = :calc_tipo
                  AND EXISTS (
                        SELECT 1 FROM taxas t
                        WHERE t.ec = vendas_calculos.ec_id
                        AND LOWER(t.bandeira) = LOWER(vendas_calculos.bandeira)
                        AND LOWER(t.forma_pagamento) = LOWER(vendas_calculos.forma_pagamento)
                        AND vendas_calculos.calc_data BETWEEN t.data_ini AND t.data_fim
                  )
            """)
            self.db.execute(sql_cad, {"calc_id": req.processamento_id, "calc_tipo": req.tipo_taxa})

        # 4. Final values calculation (Desc, Liq, Perda)
        # Update derived columns based on tx_calc
        sql_final = text("""
            UPDATE vendas_calculos
            SET
                desc_calc = (vl_venda * tx_calc / 100),
                vl_liq_calc = (vl_venda - (vl_venda * tx_calc / 100)),
                perda = (vl_liq_venda - (vl_venda - (vl_venda * tx_calc / 100)))
            WHERE calc_id = :calc_id AND calc_tipo = :calc_tipo AND tx_calc IS NOT NULL
        """)
        self.db.execute(sql_final, {"calc_id": req.processamento_id, "calc_tipo": req.tipo_taxa})

        self.db.commit()

    def listar_resultados(self, calc_id_or_pid: str, skip: int = 0, limit: int = 100):
        # We try to match by calc_id first, then fallback to proc_id if no results (for legacy)
        results = self.db.query(VendasCalculos)\
            .filter(VendasCalculos.calc_id == calc_id_or_pid)\
            .order_by(VendasCalculos.perda.asc())\
            .offset(skip).limit(limit).all()

        if not results:
             # Fallback to see if any calculation exists for this processamento_id as calc_id
             return self.db.query(VendasCalculos)\
                .filter(VendasCalculos.calc_id == calc_id_or_pid)\
                .order_by(VendasCalculos.perda.asc())\
                .offset(skip).limit(limit).all()
        return results

    def listar_historico(self, skip: int = 0, limit: int = 50):
        # Returns summary of unique calculations
        sql = text("""
            SELECT
                calc_id, calc_tipo, calc_usuario, MAX(calc_data) as calc_data,
                COUNT(*) as total_registros,
                SUM(vl_venda) as total_valor,
                SUM(perda) as perda_total
            FROM vendas_calculos
            GROUP BY calc_id, calc_tipo, calc_usuario
            ORDER BY calc_data DESC
            LIMIT :limit OFFSET :offset
        """)
        return self.db.execute(sql, {"limit": limit, "offset": skip}).fetchall()

    def analisar_periodos(
        self, processamento_id: str, threshold: float = 0.5
    ) -> AnalisePeriodosResponse:
        from app.models.vendas import Venda

        # Escolhe tabela: vendas_calculos se houver dados, senão vendas_processadas
        has_calc = (
            self.db.query(VendasCalculos)
            .filter(VendasCalculos.calc_id == processamento_id)
            .first()
        ) is not None
        model = VendasCalculos if has_calc else Venda
        pid_col = VendasCalculos.calc_id if has_calc else Venda.processamentoid
        date_col = VendasCalculos.data_venda if has_calc else Venda.data_venda
        value_col = VendasCalculos.vl_venda if has_calc else Venda.valor_venda

        # Agrupamento por mês — SQLite usa strftime
        if self.dialect == "sqlite":
            periodo_expr = func.strftime("%Y-%m", date_col).label("periodo")
        else:
            periodo_expr = func.date_format(date_col, "%Y-%m").label("periodo")

        rows = (
            self.db.query(
                periodo_expr,
                func.count().label("quantidade"),
                func.sum(value_col).label("valor_total"),
            )
            .filter(pid_col == processamento_id)
            .group_by(periodo_expr)
            .order_by(periodo_expr)
            .all()
        )

        if not rows:
            return AnalisePeriodosResponse(
                processamento_id=processamento_id,
                total_periodos=0,
                periodos_ausentes=0,
                periodos_reduzidos=0,
                mediana_quantidade=0.0,
                periodos=[],
            )

        dados_map = {r.periodo: r for r in rows if r.periodo}
        quantidades = [r.quantidade for r in rows if r.quantidade and r.quantidade > 0]
        mediana = statistics.median(quantidades) if quantidades else 0.0

        min_periodo = min(dados_map.keys())
        max_periodo = max(dados_map.keys())

        # Gera todos os meses do intervalo sem lacunas
        def _gerar_meses(start_str: str, end_str: str) -> list:
            cur = date.fromisoformat(start_str + "-01")
            end = date.fromisoformat(end_str + "-01")
            meses = []
            while cur <= end:
                meses.append(cur.strftime("%Y-%m"))
                cur += relativedelta(months=1)
            return meses

        todos_meses = _gerar_meses(min_periodo, max_periodo)
        resultado = []
        for mes in todos_meses:
            if mes not in dados_map:
                status = "ausente"
                qtd, total = 0, 0.0
            else:
                r = dados_map[mes]
                qtd = r.quantidade or 0
                total = float(r.valor_total or 0)
                if qtd < mediana * threshold:
                    status = "reduzido"
                else:
                    status = "ok"
            resultado.append(
                PeriodoAnalise(periodo=mes, quantidade=qtd, valor_total=total, status=status)
            )

        ausentes = sum(1 for p in resultado if p.status == "ausente")
        reduzidos = sum(1 for p in resultado if p.status == "reduzido")

        return AnalisePeriodosResponse(
            processamento_id=processamento_id,
            total_periodos=len(resultado),
            periodos_ausentes=ausentes,
            periodos_reduzidos=reduzidos,
            mediana_quantidade=float(mediana),
            periodos=resultado,
        )

    def deletar_calculo(self, calc_id: str):
        self.db.query(VendasCalculos).filter(VendasCalculos.calc_id == calc_id).delete(synchronize_session=False)
        self.db.commit()

