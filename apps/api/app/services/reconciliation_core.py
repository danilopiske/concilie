"""
Reconciliation engine using Polars for high-performance tax calculation.
Migrated from modules/reconciliation_core.py — no legacy sys.path dependency.
"""
import logging
import time
from contextlib import contextmanager
from datetime import datetime
from typing import Any, Dict, Optional

import pandas as pd
import polars as pl
from sqlalchemy import text
from sqlalchemy.engine import Engine

logger = logging.getLogger(__name__)


@contextmanager
def _perf_timer(label: str):
    t = time.perf_counter()
    yield
    logger.info("%s: %.4fs", label, time.perf_counter() - t)


class ReconciliationCore:
    @staticmethod
    def calculate_rates(
        engine: Engine,
        proc_id: str,
        tipo_taxa: str,
        usar_taxa_cad: bool = True,
        tem_receba_rapido: bool = False,
        progress_callback=None,
        custom_calc_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Executa o cálculo de taxas e reconciliação usando Polars para performance máxima.
        Usa Parameter Binding para segurança e evita injeção SQL.
        """
        with _perf_timer(f"RECONCILIATION Cálculo de Taxas (Polars) proc={proc_id} tipo={tipo_taxa}"):
            t_start = time.time()
            logger.info("[RECON-CORE] Iniciando cálculo Polars para Processamento %s (%s)", proc_id, tipo_taxa)
            if progress_callback:
                progress_callback(5, "Iniciando reconciliação...")

            try:
                # 1. Carregar Vendas (Filtradas por Processamento)
                query_vendas = text("""
                    SELECT id as id_venda, Bandeira, Forma_de_pagamento, data_processamento,
                           Data_da_venda, Adquirente,
                           Valor_da_venda, Valor_líquido_da_venda, Quantidade_de_parcelas,
                           ec_id, Taxas_Perc, Valor_descontado, Taxas_RR, Valor_RR,
                           arquivo_origem, NSU, Código_de_autorização as cod_autor_orig
                    FROM vendas_processadas
                    WHERE processamentoid = :proc_id
                """)

                schema_vendas = {
                    "id_venda": pl.Int64,
                    "Bandeira": pl.String,
                    "Forma_de_pagamento": pl.String,
                    "data_processamento": pl.String,
                    "Data_da_venda": pl.String,
                    "Adquirente": pl.String,
                    "Valor_da_venda": pl.Float64,
                    "Valor_líquido_da_venda": pl.Float64,
                    "Quantidade_de_parcelas": pl.Int64,
                    "ec_id": pl.String,
                    "Taxas_Perc": pl.Float64,
                    "Valor_descontado": pl.Float64,
                    "Taxas_RR": pl.Float64,
                    "Valor_RR": pl.Float64,
                    "arquivo_origem": pl.String,
                    "NSU": pl.String,
                    "cod_autor_orig": pl.String,
                }

                if progress_callback:
                    progress_callback(10, "Carregando vendas do banco...")

                with _perf_timer("RECONCILIATION Carregar Vendas (DB)"):
                    with engine.connect() as conn:
                        df_pd = pd.read_sql(query_vendas, conn, params={"proc_id": proc_id})

                        if df_pd.empty:
                            return {
                                "success": False,
                                "error": f"Nenhuma venda encontrada para o processamento {proc_id}.",
                            }

                        df_vendas = pl.from_pandas(df_pd, schema_overrides=schema_vendas)

                logger.info("[RECON-CORE] %d vendas carregadas.", len(df_vendas))
                if progress_callback:
                    progress_callback(20, f"{len(df_vendas)} vendas carregadas.")

                # 2. Normalizar e Preparar Dados
                df_vendas = df_vendas.with_columns([
                    pl.col("Data_da_venda").cast(pl.String).str.slice(0, 10).str.to_date().alias("Data_da_venda"),
                    pl.col("Bandeira").fill_null("Desconhecida").str.to_lowercase().str.strip_chars().alias("bandeira_clean"),
                    pl.col("Forma_de_pagamento").fill_null("Desconhecida").str.to_lowercase().str.strip_chars().alias("forma_pgto_clean"),
                    pl.col("Adquirente").fill_null("Desconhecida").str.to_lowercase().str.strip_chars().alias("adquirente_clean"),
                    pl.lit(custom_calc_id or proc_id).alias("calc_id"),
                    pl.lit(tipo_taxa).alias("calc_tipo"),
                    pl.lit("sistema_polars").alias("calc_usuario"),
                    pl.lit(datetime.now()).alias("calc_data"),
                ])

                # 3. Lógica de Período para o LOG
                if progress_callback:
                    progress_callback(30, "Preparando períodos de LOG...")
                if tipo_taxa == "log_mensal":
                    df_vendas = df_vendas.with_columns(pl.col("Data_da_venda").dt.truncate("1mo").alias("periodo_log"))
                elif tipo_taxa == "log_trimestral":
                    df_vendas = df_vendas.with_columns(pl.col("Data_da_venda").dt.truncate("3mo").alias("periodo_log"))
                elif tipo_taxa == "log_semestral":
                    df_vendas = df_vendas.with_columns(pl.col("Data_da_venda").dt.truncate("6mo").alias("periodo_log"))
                else:  # Anual
                    df_vendas = df_vendas.with_columns(pl.col("Data_da_venda").dt.truncate("1y").alias("periodo_log"))

                # 4. Aplicação de Taxas CAD (Opcional)
                df_vendas = df_vendas.with_columns([
                    pl.lit(None).cast(pl.Float64).alias("tx_calc"),
                    pl.lit(None).cast(pl.Float64).alias("tx_rr_calc"),
                ])

                if usar_taxa_cad:
                    logger.info("[RECON-CORE] Aplicando Taxas CAD...")
                    if progress_callback:
                        progress_callback(40, "Cruzando com Taxas Cadastradas...")

                    with engine.connect() as conn:
                        df_taxas = pl.read_database(query="SELECT * FROM taxas", connection=conn)

                    if not df_taxas.is_empty():
                        df_taxas = df_taxas.with_columns([
                            pl.col("bandeira").str.to_lowercase().str.strip_chars().alias("bandeira_clean"),
                            pl.col("forma_pagamento").str.to_lowercase().str.strip_chars().alias("forma_pgto_clean"),
                            pl.col("contexto").str.to_lowercase().str.strip_chars().alias("adquirente_clean"),
                            pl.col("data_ini").cast(pl.Date, strict=False),
                            pl.col("data_fim").cast(pl.Date, strict=False),
                            pl.col("ec").cast(pl.String).alias("ec_str"),
                        ])

                        df_vendas = df_vendas.with_columns(pl.col("ec_id").cast(pl.String).alias("ec_id_str"))

                        df_joined = df_vendas.join(
                            df_taxas.filter(pl.col("bandeira_clean").is_not_null()),
                            left_on=["ec_id_str", "adquirente_clean", "bandeira_clean", "forma_pgto_clean"],
                            right_on=["ec_str", "adquirente_clean", "bandeira_clean", "forma_pgto_clean"],
                            how="left",
                            suffix="_taxa",
                        ).filter(
                            (pl.col("tx_calc").is_null())
                            & (pl.col("Data_da_venda") >= pl.col("data_ini"))
                            & (pl.col("Data_da_venda") <= pl.col("data_fim"))
                        )

                        if not df_joined.is_empty():
                            df_vendas = df_vendas.join(
                                df_joined.select(["id_venda", "taxa"]),
                                on="id_venda",
                                how="left",
                            ).with_columns([
                                pl.coalesce([pl.col("taxa"), pl.col("tx_calc")]).alias("tx_calc")
                            ]).drop(["taxa"])

                # 5. Lógica de LOG (Min Taxa do Período)
                logger.info("[RECON-CORE] Aplicando lógica de LOG...")
                if progress_callback:
                    progress_callback(60, "Aplicando lógica de menor taxa (LOG)...")

                df_log_map = df_vendas.group_by(["periodo_log", "forma_pgto_clean", "bandeira_clean"]).agg(
                    pl.col("Taxas_Perc").min().alias("min_tx_venda"),
                    pl.col("Taxas_RR").min().alias("min_tx_rr_venda"),
                )

                df_vendas = df_vendas.join(df_log_map, on=["periodo_log", "forma_pgto_clean", "bandeira_clean"], how="left")

                df_vendas = df_vendas.with_columns([
                    pl.when(pl.col("tx_calc").is_null())
                    .then(pl.col("min_tx_venda"))
                    .otherwise(pl.col("tx_calc"))
                    .alias("tx_calc"),
                    pl.when(pl.col("tx_rr_calc").is_null())
                    .then(pl.col("min_tx_rr_venda"))
                    .otherwise(pl.col("tx_rr_calc"))
                    .alias("tx_rr_calc"),
                ])

                # 6. Cálculos Financeiros Finais
                logger.info("[RECON-CORE] Calculando valores financeiros...")
                if progress_callback:
                    progress_callback(80, "Calculando discrepâncias e perdas...")
                df_vendas = df_vendas.with_columns([
                    (pl.col("Valor_da_venda") * pl.col("tx_calc").fill_null(0) / 100).alias("desc_calc"),
                    (pl.col("Valor_da_venda") * pl.col("tx_rr_calc").fill_null(0) / 100).alias("vl_rr_calc"),
                ]).with_columns([
                    (pl.col("Valor_da_venda") - pl.col("desc_calc")).alias("vl_liq_calc"),
                    pl.when((pl.col("Taxas_Perc").is_null()) | (pl.col("Taxas_Perc") == 0))
                    .then(0.0)
                    .otherwise(pl.col("Valor_líquido_da_venda") - (pl.col("Valor_da_venda") - pl.col("desc_calc")))
                    .alias("perda"),
                ])

                if tem_receba_rapido:
                    df_vendas = df_vendas.with_columns([
                        (pl.col("vl_rr_calc") - pl.col("Valor_RR").fill_null(0)).alias("perda_rr")
                    ])
                else:
                    df_vendas = df_vendas.with_columns([
                        pl.lit(0.0).alias("tx_rr_calc"),
                        pl.lit(0.0).alias("vl_rr_calc"),
                        pl.lit(0.0).alias("perda_rr"),
                    ])

                # 7. Limpeza e Escrita Final
                df_final = df_vendas.select([
                    pl.col("id_venda"),
                    pl.col("calc_id"),
                    pl.col("calc_tipo"),
                    pl.col("calc_usuario"),
                    pl.col("Bandeira").alias("bandeira"),
                    pl.col("Forma_de_pagamento").alias("forma_pagamento"),
                    pl.col("calc_data"),
                    pl.col("Data_da_venda").alias("data_venda"),
                    pl.col("ec_id"),
                    pl.col("Adquirente").alias("adquirente"),
                    pl.col("arquivo_origem"),
                    pl.col("NSU").alias("nsu"),
                    pl.col("cod_autor_orig").alias("cod_autorizacao"),
                    pl.col("Valor_da_venda").alias("vl_venda"),
                    pl.col("Taxas_Perc").alias("tx_venda"),
                    (pl.col("Valor_da_venda") * pl.col("Taxas_Perc").fill_null(0) / 100).alias("desc_venda"),
                    pl.col("Valor_líquido_da_venda").alias("vl_liq_venda"),
                    pl.col("Taxas_RR").alias("tx_rr_venda"),
                    pl.col("Valor_RR").alias("vl_rr_venda"),
                    pl.col("tx_calc"),
                    pl.col("desc_calc"),
                    pl.col("vl_liq_calc"),
                    pl.col("tx_rr_calc"),
                    pl.col("vl_rr_calc"),
                    pl.col("perda"),
                    pl.col("perda_rr"),
                ])

                logger.info("[RECON-CORE] Preparado para inserir %d registros.", len(df_final))
                if progress_callback:
                    progress_callback(90, "Salvando resultados no banco de dados...")

                with _perf_timer(f"RECONCILIATION Salvar Resultados (DB) rows={len(df_final)}"):
                    with engine.begin() as conn:
                        df_final.to_pandas().to_sql(
                            "vendas_calculos",
                            con=conn,
                            if_exists="append",
                            index=False,
                            chunksize=10000,
                        )

                t_total = time.time() - t_start
                logger.info("[RECON-CORE] Concluído com Sucesso em %.2fs!", t_total)
                if progress_callback:
                    progress_callback(100, f"Cálculo concluído em {t_total:.2f}s.")

                return {"success": True, "time": t_total, "rows": len(df_final)}

            except Exception as e:
                logger.exception("[RECON-CORE] Erro no motor Polars")
                return {"success": False, "error": f"Erro no motor Polars: {str(e)}"}
