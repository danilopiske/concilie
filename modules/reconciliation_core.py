import polars as pl
import pandas as pd
from sqlalchemy import text, Engine
import time
from datetime import datetime
from typing import Dict, Any, Optional

class ReconciliationCore:
    @staticmethod
    def calculate_rates(engine: Engine, proc_id: int, tipo_taxa: str, usar_taxa_cad: bool = True, tem_receba_rapido: bool = False) -> Dict[str, Any]:
        """
        Executa o cálculo de taxas e reconciliação usando Polars para performance máxima.
        Substitui múltiplos UPDATE JOINs por cruzamento em memória.
        """
        t_start = time.time()
        print(f"[RECON-CORE] Iniciando cálculo Polars para Processamento {proc_id} ({tipo_taxa})")

        try:
            # 1. Carregar Vendas (Filtradas por Processamento)
            query_vendas = f"""
                SELECT id as id_venda, Bandeira, Forma_de_pagamento, data_processamento, 
                       Data_da_venda, Adquirente,
                       Valor_da_venda, Valor_líquido_da_venda, Quantidade_de_parcelas, 
                       ec_id, Taxas_Perc, Valor_descontado, Taxas_RR, Valor_RR,
                       arquivo_origem, NSU, Código_de_autorização as cod_autorizacao
                FROM vendas_processadas 
                WHERE processamentoid = {proc_id}
            """
            
            df_vendas = pl.read_database(query=query_vendas, connection=engine.connect())
            if df_vendas.is_empty():
                return {"success": False, "error": "Nenhuma venda encontrada."}

            print(f"[RECON-CORE] {len(df_vendas)} vendas carregadas.")

            # 2. Normalizar e Preparar Dados
            df_vendas = df_vendas.with_columns([
                # Para SQLite, Data_da_venda vem como string "YYYY-MM-DD HH:MM:SS.SSSSSS"
                pl.col("Data_da_venda").str.slice(0, 10).str.to_date().alias("Data_da_venda"),
                pl.col("Bandeira").str.to_lowercase().str.strip_chars().alias("bandeira_clean"),
                pl.col("Forma_de_pagamento").str.to_lowercase().str.strip_chars().alias("forma_pgto_clean"),
                pl.col("Adquirente").str.to_lowercase().str.strip_chars().alias("adquirente_clean"),
                pl.lit(proc_id).alias("calc_id"),
                pl.lit(tipo_taxa).alias("calc_tipo"),
                pl.lit("sistema_polars").alias("calc_usuario"),
                pl.lit(datetime.now()).alias("calc_data")
            ])

            # 3. Lógica de Período para o LOG
            # Definir a coluna de período baseada no tipo_taxa
            if tipo_taxa == "log_mensal":
                df_vendas = df_vendas.with_columns(pl.col("Data_da_venda").dt.truncate("1mo").alias("periodo_log"))
            elif tipo_taxa == "log_trimestral":
                df_vendas = df_vendas.with_columns(pl.col("Data_da_venda").dt.truncate("3mo").alias("periodo_log"))
            elif tipo_taxa == "log_semestral":
                df_vendas = df_vendas.with_columns(pl.col("Data_da_venda").dt.truncate("6mo").alias("periodo_log"))
            else: # Anual
                df_vendas = df_vendas.with_columns(pl.col("Data_da_venda").dt.truncate("1y").alias("periodo_log"))

            # 4. Aplicação de Taxas CAD (Opcional)
            df_vendas = df_vendas.with_columns([
                pl.lit(None).cast(pl.Float64).alias("tx_calc"),
                pl.lit(None).cast(pl.Float64).alias("tx_rr_calc")
            ])

            if usar_taxa_cad:
                print("[RECON-CORE] Aplicando Taxas CAD...")
                df_taxas = pl.read_database(query="SELECT * FROM taxas", connection=engine.connect())
                if not df_taxas.is_empty():
                    df_taxas = df_taxas.with_columns([
                        pl.col("bandeira").str.to_lowercase().str.strip_chars().alias("bandeira_clean"),
                        pl.col("forma_pagamento").str.to_lowercase().str.strip_chars().alias("forma_pgto_clean"),
                        pl.col("contexto").str.to_lowercase().str.strip_chars().alias("adquirente_clean"),
                        pl.col("data_ini").cast(pl.Date),
                        pl.col("data_fim").cast(pl.Date),
                        # Garantir que ec seja i64 para o join
                        pl.col("ec").cast(pl.Int64, strict=False)
                    ])

                    # Join Vendas x Taxas (Camada 1: Específica)
                    # Note: Polars doesn't do "between" join natively yet in a single step easily
                    # Garantir que ec_id seja i64
                    df_vendas = df_vendas.with_columns(pl.col("ec_id").cast(pl.Int64))

                    df_joined = df_vendas.join(
                        df_taxas.filter(pl.col("bandeira_clean").is_not_null()),
                        left_on=["ec_id", "adquirente_clean", "bandeira_clean", "forma_pgto_clean"],
                        right_on=["ec", "adquirente_clean", "bandeira_clean", "forma_pgto_clean"],
                        how="left",
                        suffix="_taxa"
                    ).filter(
                        (pl.col("tx_calc").is_null()) & 
                        (pl.col("Data_da_venda") >= pl.col("data_ini")) & 
                        (pl.col("Data_da_venda") <= pl.col("data_fim"))
                    )

                    # Se encontrarmos matches, atualizamos no DF original
                    if not df_joined.is_empty():
                        # Usamos join + update
                        df_vendas = df_vendas.join(
                            df_joined.select(["id_venda", "taxa", "taxa_rr"]),
                            on="id_venda",
                            how="left"
                        ).with_columns([
                            pl.col("taxa").alias("tx_calc"),
                            pl.col("taxa_rr").alias("tx_rr_calc")
                        ]).drop(["taxa", "taxa_rr"])

            # 5. Lógica de LOG (Min Taxa do Período)
            print("[RECON-CORE] Aplicando lógica de LOG...")
            # Calcular a menor taxa por grupo de (periodo, forma, bandeira)
            df_log_map = df_vendas.group_by(["periodo_log", "forma_pgto_clean", "bandeira_clean"]).agg(
                pl.col("Taxas_Perc").min().alias("min_tx_venda"),
                pl.col("Taxas_RR").min().alias("min_tx_rr_venda")
            )

            # Preencher onde tx_calc ainda é nulo
            df_vendas = df_vendas.join(df_log_map, on=["periodo_log", "forma_pgto_clean", "bandeira_clean"], how="left")
            
            df_vendas = df_vendas.with_columns([
                pl.when(pl.col("tx_calc").is_null())
                .then(pl.col("min_tx_venda"))
                .otherwise(pl.col("tx_calc"))
                .alias("tx_calc"),
                
                pl.when(pl.col("tx_rr_calc").is_null())
                .then(pl.col("min_tx_rr_venda"))
                .otherwise(pl.col("tx_rr_calc"))
                .alias("tx_rr_calc")
            ])

            # 6. Cálculos Financeiros Finais
            print("[RECON-CORE] Calculando valores financeiros...")
            df_vendas = df_vendas.with_columns([
                # vl_venda * tx_calc / 100
                (pl.col("Valor_da_venda") * pl.col("tx_calc").fill_null(0) / 100).alias("desc_calc"),
                # vl_venda * tx_rr_calc / 100
                (pl.col("Valor_da_venda") * pl.col("tx_rr_calc").fill_null(0) / 100).alias("vl_rr_calc")
            ]).with_columns([
                # vl_venda - desc_calc
                (pl.col("Valor_da_venda") - pl.col("desc_calc")).alias("vl_liq_calc"),
                # Perda = Original - Calculado
                # Se tx_venda for 0 ou nula, perda é 0 (lógica do sistema legado)
                pl.when((pl.col("Taxas_Perc").is_null()) | (pl.col("Taxas_Perc") == 0))
                .then(0.0)
                .otherwise(pl.col("Valor_líquido_da_venda") - (pl.col("Valor_da_venda") - pl.col("desc_calc")))
                .alias("perda")
            ])

            if tem_receba_rapido:
                df_vendas = df_vendas.with_columns([
                    # Perda RR = Calculado - Original (conforme lógica ui_calculos.py linha 948)
                    (pl.col("vl_rr_calc") - pl.col("Valor_RR").fill_null(0)).alias("perda_rr")
                ])
            else:
                df_vendas = df_vendas.with_columns([
                    pl.lit(0.0).alias("tx_rr_calc"),
                    pl.lit(0.0).alias("vl_rr_calc"),
                    pl.lit(0.0).alias("perda_rr")
                ])

            # 7. Limpeza e Escrita Final
            # Mapear colunas para o banco de dados target (vendas_calculos)
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
                pl.col("cod_autorizacao"),
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
                pl.col("perda_rr")
            ])

            print(f"[RECON-CORE] Preparado para inserir {len(df_final)} registros.")

            # Limpar dados antigos antes de inserir novos
            with engine.begin() as conn:
                conn.execute(text(f"DELETE FROM vendas_calculos WHERE calc_id = {proc_id} AND calc_tipo = '{tipo_taxa}'"))
                
                # Converter para pandas apenas para escrita via SQLAlchemy (mais seguro para tipos de dados complexos no SQLite)
                # ou usar df.write_database se configurado.
                df_final.to_pandas().to_sql("vendas_calculos", con=conn, if_exists="append", index=False)

            t_total = time.time() - t_start
            print(f"[RECON-CORE] Concluido com Sucesso em {t_total:.2f}s!")
            
            return {
                "success": True,
                "time": t_total,
                "rows": len(df_final)
            }

        except Exception as e:
            import traceback
            traceback.print_exc()
            return {"success": False, "error": str(e)}

if __name__ == "__main__":
    # Teste rápido se executado diretamente
    from app.core.database import engine
    res = ReconciliationCore.calculate_rates(engine, 1, "log_mensal")
    print(res)
