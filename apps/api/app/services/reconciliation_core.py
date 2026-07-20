"""
Reconciliation engine using Polars for high-performance tax calculation.
Migrated from modules/reconciliation_core.py — no legacy sys.path dependency.
"""
import glob
import logging
import os
import time
from contextlib import contextmanager
from datetime import datetime
from typing import Any, Dict, Optional

import pandas as pd
import polars as pl
from sqlalchemy import text
from sqlalchemy.engine import Engine

logger = logging.getLogger(__name__)


def _normalize_str(col: pl.Expr) -> pl.Expr:
    """Lowercase + strip + remove Portuguese accents for consistent joins."""
    return (
        col.fill_null("Desconhecida")
        .str.to_lowercase()
        .str.strip_chars()
        .str.replace_all(r"[áàâã]", "a")
        .str.replace_all(r"[éê]", "e")
        .str.replace_all(r"í", "i")
        .str.replace_all(r"[óôõ]", "o")
        .str.replace_all(r"ú", "u")
        .str.replace_all(r"ç", "c")
    )


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
                    _normalize_str(pl.col("Bandeira")).alias("bandeira_clean"),
                    _normalize_str(pl.col("Forma_de_pagamento")).alias("forma_pgto_clean"),
                    _normalize_str(pl.col("Adquirente")).alias("adquirente_clean"),
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

                # 4. Aplicação de Taxas (CAD + Contrato)
                df_vendas = df_vendas.with_columns([
                    pl.lit(None).cast(pl.Float64).alias("tx_calc"),
                    pl.lit(None).cast(pl.Float64).alias("tx_rr_calc"),
                    pl.lit(None).cast(pl.String).alias("calc_origem"),
                ])

                if usar_taxa_cad:
                    logger.info("[RECON-CORE] Aplicando Taxas CAD...")
                    if progress_callback:
                        progress_callback(40, "Cruzando com Taxas Cadastradas...")

                    # 4.0: Taxas Contratadas (prioridade máxima)
                    try:
                        with engine.connect() as conn:
                            _cli_row = conn.execute(
                                text("""
                                    SELECT ec.cliente_id
                                    FROM ecs_cliente ec
                                    JOIN vendas_processadas vp
                                      ON CAST(vp.ec_id AS CHAR) = CAST(ec.ec_id AS CHAR)
                                    WHERE vp.processamentoid = :pid
                                    LIMIT 1
                                """),
                                {"pid": proc_id},
                            ).fetchone()
                            _cliente_id = int(_cli_row[0]) if _cli_row else None

                        if _cliente_id:
                            with engine.connect() as conn:
                                df_tc = pl.read_database(
                                    query=(
                                        "SELECT bandeira, modalidade, taxa_contratada, "
                                        "vigencia_inicio, vigencia_fim "
                                        f"FROM taxas_contratadas WHERE cliente_id = {_cliente_id}"
                                    ),
                                    connection=conn,
                                )
                            if not df_tc.is_empty():
                                df_tc = df_tc.with_columns([
                                    _normalize_str(pl.col("bandeira")).alias("bandeira_clean"),
                                    _normalize_str(pl.col("modalidade")).alias("forma_pgto_clean"),
                                    pl.col("vigencia_inicio").cast(pl.Date, strict=False),
                                    pl.col("vigencia_fim").cast(pl.Date, strict=False),
                                ])
                                joined_tc = df_vendas.join(
                                    df_tc.select(["bandeira_clean", "forma_pgto_clean", "taxa_contratada", "vigencia_inicio", "vigencia_fim"]),
                                    on=["bandeira_clean", "forma_pgto_clean"],
                                    how="left",
                                    suffix="_tc",
                                ).filter(
                                    pl.col("tx_calc").is_null()
                                    & pl.col("taxa_contratada").is_not_null()
                                    & (pl.col("Data_da_venda") >= pl.col("vigencia_inicio"))
                                    & (pl.col("vigencia_fim").is_null() | (pl.col("Data_da_venda") <= pl.col("vigencia_fim")))
                                )
                                if not joined_tc.is_empty():
                                    df_vendas = df_vendas.join(
                                        joined_tc.select(["id_venda", "taxa_contratada"]).unique("id_venda"),
                                        on="id_venda",
                                        how="left",
                                    ).with_columns([
                                        pl.coalesce([pl.col("taxa_contratada"), pl.col("tx_calc")]).alias("tx_calc"),
                                        pl.when(pl.col("taxa_contratada").is_not_null())
                                        .then(pl.lit("contrato"))
                                        .otherwise(pl.col("calc_origem"))
                                        .alias("calc_origem"),
                                    ]).drop(["taxa_contratada"])
                                logger.info("[RECON-CORE] Taxas contratadas aplicadas.")
                    except Exception as _e:
                        logger.warning("[RECON-CORE] Taxas contratadas não aplicadas: %s", _e)

                    # 4.1: Taxas CAD legado (fallback para vazios)
                    with engine.connect() as conn:
                        df_taxas = pl.read_database(query="SELECT * FROM taxas", connection=conn)

                    if not df_taxas.is_empty():
                        df_taxas = df_taxas.with_columns([
                            _normalize_str(pl.col("bandeira")).alias("bandeira_clean"),
                            _normalize_str(pl.col("forma_pagamento")).alias("forma_pgto_clean"),
                            pl.col("contexto").str.to_lowercase().str.strip_chars().alias("contexto_clean"),
                            pl.col("data_ini").cast(pl.Date, strict=False),
                            pl.col("data_fim").cast(pl.Date, strict=False),
                            pl.col("ec").cast(pl.String).alias("ec_str"),
                        ])

                        df_vendas = df_vendas.with_columns(pl.col("ec_id").cast(pl.String).alias("ec_id_str"))

                        def _apply_taxas(df_v: pl.DataFrame, df_t: pl.DataFrame) -> pl.DataFrame:
                            """Tenta match por adquirente exato; fallback para contexto='padrao'. Só preenche tx_calc nulo."""
                            # Passe 1: match exato por adquirente
                            df_t_especifica = df_t.filter(pl.col("contexto_clean") != "padrao")
                            joined1 = df_v.join(
                                df_t_especifica.filter(pl.col("bandeira_clean").is_not_null()),
                                left_on=["ec_id_str", "adquirente_clean", "bandeira_clean", "forma_pgto_clean"],
                                right_on=["ec_str", "contexto_clean", "bandeira_clean", "forma_pgto_clean"],
                                how="left",
                                suffix="_taxa",
                            ).filter(
                                (pl.col("tx_calc").is_null())
                                & (pl.col("Data_da_venda") >= pl.col("data_ini"))
                                & (pl.col("Data_da_venda") <= pl.col("data_fim"))
                            )
                            if not joined1.is_empty():
                                df_v = df_v.join(
                                    joined1.select(["id_venda", "taxa"]),
                                    on="id_venda",
                                    how="left",
                                ).with_columns([
                                    pl.coalesce([pl.col("taxa"), pl.col("tx_calc")]).alias("tx_calc")
                                ]).drop(["taxa"])

                            # Passe 2: fallback contexto='padrao' para os ainda sem taxa
                            df_t_padrao = df_t.filter(pl.col("contexto_clean") == "padrao")
                            if not df_t_padrao.is_empty():
                                joined2 = df_v.join(
                                    df_t_padrao.filter(pl.col("bandeira_clean").is_not_null()),
                                    left_on=["ec_id_str", "bandeira_clean", "forma_pgto_clean"],
                                    right_on=["ec_str", "bandeira_clean", "forma_pgto_clean"],
                                    how="left",
                                    suffix="_taxa",
                                ).filter(
                                    (pl.col("tx_calc").is_null())
                                    & (pl.col("Data_da_venda") >= pl.col("data_ini"))
                                    & (pl.col("Data_da_venda") <= pl.col("data_fim"))
                                )
                                if not joined2.is_empty():
                                    df_v = df_v.join(
                                        joined2.select(["id_venda", "taxa"]),
                                        on="id_venda",
                                        how="left",
                                    ).with_columns([
                                        pl.coalesce([pl.col("taxa"), pl.col("tx_calc")]).alias("tx_calc")
                                    ]).drop(["taxa"])

                            return df_v

                        df_vendas = _apply_taxas(df_vendas, df_taxas)

                        # Marcar origem='cad' para os preenchidos neste passo
                        df_vendas = df_vendas.with_columns([
                            pl.when(pl.col("calc_origem").is_null() & pl.col("tx_calc").is_not_null())
                            .then(pl.lit("cad"))
                            .otherwise(pl.col("calc_origem"))
                            .alias("calc_origem"),
                        ])

                # 5. Lógica de LOG (Min Taxa do Período)
                logger.info("[RECON-CORE] Aplicando lógica de LOG...")
                if progress_callback:
                    progress_callback(60, "Aplicando lógica de menor taxa (LOG)...")

                df_log_map = df_vendas.group_by(["periodo_log", "forma_pgto_clean", "bandeira_clean"]).agg(
                    pl.col("Taxas_Perc").min().alias("min_tx_venda"),
                    # ⚠️ Ignorar Taxas_RR = 0 ao calcular a menor taxa do período: a maioria
                    # das vendas de um grupo (bandeira+forma+período) não usa Receba Rápido,
                    # então incluir essas taxas zeradas no min() sempre resultava em 0,00%,
                    # tornando a opção "menor do período" inútil para RR.
                    pl.col("Taxas_RR").filter(pl.col("Taxas_RR") > 0).min().alias("min_tx_rr_venda"),
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
                    # Marcar origem='log' para os que não tiveram taxa CAD/contrato
                    pl.when(pl.col("calc_origem").is_null())
                    .then(pl.lit("log"))
                    .otherwise(pl.col("calc_origem"))
                    .alias("calc_origem"),
                ])

                # 6. Cálculos Financeiros Finais
                logger.info("[RECON-CORE] Calculando valores financeiros...")
                if progress_callback:
                    progress_callback(80, "Calculando discrepâncias e perdas...")
                df_vendas = df_vendas.with_columns([
                    (pl.col("Valor_da_venda") * pl.col("tx_calc").fill_null(0) / 100).alias("desc_calc"),
                    (pl.col("Valor_da_venda") * pl.col("tx_rr_calc").fill_null(0) / 100).alias("vl_rr_calc"),
                    # desc_venda real: 1) Valor_descontado abs (MDR real cobrado)  2) Taxas_Perc  3) derivar do líquido
                    pl.when(pl.col("Valor_descontado").is_not_null() & (pl.col("Valor_descontado") != 0))
                    .then(pl.col("Valor_descontado").abs())
                    .when(pl.col("Taxas_Perc").is_not_null() & (pl.col("Taxas_Perc") != 0))
                    .then(pl.col("Valor_da_venda") * pl.col("Taxas_Perc") / 100)
                    .otherwise(
                        pl.col("Valor_da_venda") - pl.col("Valor_líquido_da_venda") - pl.col("Valor_RR").fill_null(0)
                    )
                    .alias("desc_venda_real"),
                ]).with_columns([
                    (pl.col("Valor_da_venda") - pl.col("desc_calc")).alias("vl_liq_calc"),
                    # perda = só MDR: taxa contratada − o que a adquirente realmente cobrou
                    pl.when(
                        (pl.col("tx_calc").is_null()) | (pl.col("tx_calc") == 0)
                    )
                    .then(0.0)
                    .otherwise(pl.col("desc_calc") - pl.col("desc_venda_real"))
                    .alias("perda"),
                ])

                if tem_receba_rapido:
                    # Perda = o que o contrato permite - o que foi cobrado; nunca positivo
                    df_vendas = df_vendas.with_columns([
                        pl.min_horizontal(
                            pl.col("vl_rr_calc") - pl.col("Valor_RR").fill_null(0.0),
                            pl.lit(0.0)
                        ).alias("perda_rr")
                    ])
                else:
                    # RR não incluso no cálculo: todo Valor_RR cobrado é perda integral (negativo)
                    df_vendas = df_vendas.with_columns([
                        pl.lit(0.0).alias("tx_rr_calc"),
                        pl.lit(0.0).alias("vl_rr_calc"),
                        (pl.col("Valor_RR").fill_null(0.0) * -1.0).alias("perda_rr"),
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
                    pl.col("desc_venda_real").alias("desc_venda"),
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
                    pl.col("calc_origem"),
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

                # Invalidar cache Parquet do relatório para este calc_id
                _cache_dir = os.path.join(os.path.dirname(__file__), "..", "..", "relatorios_cache")
                _safe = "".join(c if c.isalnum() or c in "_-" else "_" for c in (custom_calc_id or proc_id))
                for _f in glob.glob(os.path.join(_cache_dir, f"{_safe}*.parquet")):
                    try:
                        os.remove(_f)
                        logger.info("[RECON-CORE] Cache invalidado: %s", os.path.basename(_f))
                    except OSError:
                        pass

                t_total = time.time() - t_start
                logger.info("[RECON-CORE] Concluído com Sucesso em %.2fs!", t_total)
                if progress_callback:
                    progress_callback(100, f"Cálculo concluído em {t_total:.2f}s.")

                return {"success": True, "time": t_total, "rows": len(df_final)}

            except Exception as e:
                logger.exception("[RECON-CORE] Erro no motor Polars")
                return {"success": False, "error": f"Erro no motor Polars: {str(e)}"}
