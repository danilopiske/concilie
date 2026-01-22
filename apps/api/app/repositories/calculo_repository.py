from sqlalchemy.orm import Session
from sqlalchemy import text
from app.schemas.calculo import CalculoPreviewRequest, CalculoStats, CalculoRequest
from app.models.vendas_calculos import VendasCalculos
import time
from datetime import datetime

class CalculoRepository:
    def __init__(self, db: Session):
        self.db = db
        self.dialect = self.db.bind.dialect.name

    def _get_period_formula(self, alias="vp"):
        """Returns DBMS-specific formula for 'Year-01-01'"""
        # Note: Column name is Data_da_venda in DB
        if self.dialect == 'sqlite':
            return f"strftime('%Y', {alias}.Data_da_venda) || '-01-01'"
        else:
            return f"CONCAT(YEAR({alias}.Data_da_venda), '-01-01')"

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
        # 1. Clear previous calculation for this ID/Type
        self.db.query(VendasCalculos).filter(
            VendasCalculos.calc_id == req.processamento_id,
            VendasCalculos.calc_tipo == req.tipo_taxa
        ).delete()
        self.db.commit()

        # 2. Insert Base Data (Massive Insert)
        # We insert all sales into vendas_calculos with NULL calculated fields initially
        insert_sql = text("""
            INSERT INTO vendas_calculos (
                id_venda, calc_id, calc_tipo, calc_usuario, bandeira, forma_pagamento, calc_data,
                data_venda, ec_id, adquirente, arquivo_origem,
                nsu, cod_autorizacao,
                vl_venda, tx_venda, desc_venda, vl_liq_venda,
                tx_rr_venda, vl_rr_venda,
                tx_calc, desc_calc, vl_liq_calc, tx_rr_calc, vl_rr_calc, perda, perda_rr
            )
            SELECT 
                id, :calc_id, :calc_tipo, :usuario, Bandeira, Forma_de_pagamento, :now,
                Data_da_venda, ec_id, Adquirente, arquivo_origem,
                NSU, Código_de_autorização,
                Valor_da_venda, Taxas_Perc, (Valor_da_venda * Taxas_Perc / 100), (Valor_da_venda - (Valor_da_venda * Taxas_Perc / 100)),
                Taxas_RR, (Valor_da_venda * Taxas_RR / 100),
                NULL, NULL, NULL, NULL, NULL, NULL, NULL
            FROM vendas_processadas
            WHERE processamentoid = :pid
        """)
        
        self.db.execute(insert_sql, {
            "calc_id": req.processamento_id,
            "calc_tipo": req.tipo_taxa,
            "usuario": usuario_logado,
            "now": datetime.now(),
            "pid": req.processamento_id
        })
        self.db.commit() # Commit insert before updates
        
        # 3. Apply Calculations (UPDATEs)
        
        # 3A. Taxa de Log (Minimum Rate in Period)
        # Logic: Find min(Taxas_Perc) for same EC, Bandeira, FormaPagamento in period
        # We need to port `_convert_min_tx_update_for_sqlite` logic essentially
        
        # 3A. Taxa de Log (Minimum Rate in Period)
        # Using UPDATE JOIN which is compatible with MySQL
        
        period_formula_vp = self._get_period_formula("vp")
        period_formula_vc = self._get_period_formula("vc")

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
                      AND {self._get_period_formula("vp")} = {self._get_period_formula("vendas_calculos")}
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
    
    def listar_resultados(self, calc_id: str, skip: int = 0, limit: int = 100):
        # Return paginated results, ordering by Perda (descending) to show biggest discrepancies first
        return self.db.query(VendasCalculos)\
            .filter(VendasCalculos.calc_id == calc_id)\
            .order_by(VendasCalculos.perda.asc())\
            .offset(skip).limit(limit).all()

