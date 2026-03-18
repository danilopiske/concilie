import pandas as pd
import os
from typing import Optional, Dict, Any, List
from .utils import log_with_time, safe_read_file
from sqlalchemy.engine import Engine
from datetime import datetime

class ParserError(Exception):
    """Custom exception for parsing errors."""
    pass

class BaseImporter:
    def __init__(self, engine: Engine, ec_id: str, cliente_id: int, contexto: str, usuario: str, tipo_arquivo: str = "V"):
        self.engine = engine
        self.ec_id = str(ec_id)
        self.cliente_id = cliente_id
        self.contexto = contexto
        self.usuario = usuario
        self.tipo_arquivo = tipo_arquivo # 'V' for Vendas, 'R' for Recebíveis
        self.df_raw: Optional[pd.DataFrame] = None
        self.df_mapped: Optional[pd.DataFrame] = None
        self.df_proc: Optional[pd.DataFrame] = None
        self.df_filt: Optional[pd.DataFrame] = None
        self.arquivo_origem: str = ""
        self.processamentoid: Optional[int] = None

    def log(self, message: str, type: str = "INFO"):
        log_with_time(f"[{self.__class__.__name__}] {message}", type)

    def read(self, path: str, nrows: Optional[int] = None, progress_callback=None):
        self.log(f"Iniciando leitura de {path}...")
        if progress_callback: progress_callback(10, "Lendo arquivo...")
        self.arquivo_origem = os.path.basename(path)
        self.df_raw, self.header_idx, self.columns = safe_read_file(path, nrows=nrows)
        self.log(f"Leitura concluída. {len(self.df_raw)} linhas encontradas.")
        if progress_callback: progress_callback(30, "Arquivo lido.")

    def parse(self, progress_callback=None):
        """Maps raw columns to internal standard names using De-Para rules."""
        if self.df_raw is None or self.df_raw.empty:
            self.log("Nenhum dado bruto para mapear.", "WARNING")
            self.df_proc = pd.DataFrame()
            return

        try:
            from conf.funcoesbd import depara_carregar_mapa_completo
            from proc.proc_importacao import aplicar_regras_depara
            
            self.log(f"Carregando regras de De-Para para contexto '{self.contexto}'...")
            if progress_callback: progress_callback(40, "Carregando regras De-Para...")
            regras = depara_carregar_mapa_completo(self.engine, contexto=self.contexto, tipo_origem=self.tipo_arquivo)
            
            self.log(f"Aplicando {len(regras)} regras de De-Para...")
            if progress_callback: progress_callback(50, "Mapeando colunas...")
            self.df_proc, self.transformacoes = aplicar_regras_depara(self.df_raw, regras)
            self.log(f"Mapeamento concluído. {len(self.df_proc)} linhas resultantes.")
            if progress_callback: progress_callback(70, "Mapeamento concluído.")
            
        except Exception as e:
            self.log(f"Erro no mapeamento De-Para: {str(e)}", "ERROR")
            self.df_proc = self.df_raw.copy()

    def normalize(self, progress_callback=None):
        """Standardizes data types and values."""
        if progress_callback: progress_callback(80, "Normalizando dados...")
        if self.df_proc is not None and not self.df_proc.empty:
            if "Filtrado" not in self.df_proc.columns:
                self.df_proc["Filtrado"] = 0
                
        if progress_callback: progress_callback(90, "Normalização concluída.")

    def save(self, progress_callback=None):
        """Persists data to database."""
        if self.df_proc is None:
            self.log("Nenhum dado processado para salvar.", "WARNING")
            return {"vendas": 0, "recebiveis": 0}

        try:
            from conf.funcoesbd import (
                processamento_gerar_novo_id, processamento_salvar,
                vendas_processadas_bulk_insert, vendas_filtradas_bulk_insert,
                vendas_remover_duplicadas, recebiveis_processados_bulk_insert,
                recebiveis_filtrados_bulk_insert, recebiveis_remover_duplicadas
            )

            now = datetime.now()
            if self.processamentoid is None:
                if progress_callback: progress_callback(92, "Gerando ID de processamento...")
                self.processamentoid, _ = processamento_gerar_novo_id(self.engine, self.ec_id, now)
                processamento_salvar(
                    self.engine,
                    ec_id=self.ec_id,
                    cliente_id=int(self.cliente_id),
                    id_processamento=self.processamentoid,
                    descricao=f"Importação {self.contexto or '-'} ({self.arquivo_origem})",
                    data_processamento=now,
                )

            # Metadata enrichment
            for df in [self.df_proc, self.df_filt]:
                if df is not None and not df.empty:
                    df["arquivo_origem"] = self.arquivo_origem
                    df["processamentoid"] = self.processamentoid
                    df["cliente_id"] = int(self.cliente_id)
                    df["usuario_processamento"] = self.usuario
                    if "ec_id" not in df.columns or df["ec_id"].isna().all():
                        df["ec_id"] = str(self.ec_id)

            # 1. Deduplication in memory (Polars)
            if progress_callback: progress_callback(95, "Removendo duplicadas em memória (Polars)...")
            import polars as pl
            cols_ignorar = {"id", "data_processamento", "usuario_processamento", "arquivo_origem", "processamentoid"}
            for df_key in ["df_proc", "df_filt"]:
                _df = getattr(self, df_key)
                if _df is not None and not _df.empty:
                    cols_dedup = [c for c in _df.columns if c not in cols_ignorar]
                    len_antes = len(_df)
                    _df = pl.from_pandas(_df).unique(subset=cols_dedup).to_pandas()
                    setattr(self, df_key, _df)
                    if len_antes > len(_df):
                        self.log(f"Removidas {len_antes - len(_df)} duplicadas em memória ({df_key}).")

            # 2. Bulk Insert
            if progress_callback: progress_callback(97, "Gravando no banco de dados...")
            if self.tipo_arquivo == "V":
                if not self.df_proc.empty:
                    vendas_processadas_bulk_insert(self.engine, self.df_proc)
                if self.df_filt is not None and not self.df_filt.empty:
                    vendas_filtradas_bulk_insert(self.engine, self.df_filt)
                    
                # 3. SQL Deduplication
                if not self.df_proc.empty:
                    vendas_remover_duplicadas(self.engine, "vendas_processadas", self.processamentoid, self.df_proc.columns.tolist())
                if self.df_filt is not None and not self.df_filt.empty:
                    vendas_remover_duplicadas(self.engine, "vendas_filtradas", self.processamentoid, self.df_filt.columns.tolist())
            
            elif self.tipo_arquivo == "R":
                if not self.df_proc.empty:
                    recebiveis_processados_bulk_insert(self.engine, self.df_proc)
                if self.df_filt is not None and not self.df_filt.empty:
                    recebiveis_filtrados_bulk_insert(self.engine, self.df_filt)
                
                # 3. SQL Deduplication
                if not self.df_proc.empty:
                    recebiveis_remover_duplicadas(self.engine, "recebiveis_processados", self.processamentoid, self.df_proc.columns.tolist())
                if self.df_filt is not None and not self.df_filt.empty:
                    recebiveis_remover_duplicadas(self.engine, "recebiveis_filtradas", self.processamentoid, self.df_filt.columns.tolist())

            if progress_callback: progress_callback(100, "Importação modular concluída.")
            self.log(f"Processamento modular concluído com sucesso para ID {self.processamentoid}")
            return {
                "processamentoid": self.processamentoid,
                "vendas": len(self.df_proc) if self.tipo_arquivo == "V" else 0,
                "recebiveis": len(self.df_proc) if self.tipo_arquivo == "R" else 0,
                "total": len(self.df_proc),
                "filtradas": len(self.df_filt) if self.df_filt is not None else 0
            }

        except Exception as e:
            self.log(f"Erro ao salvar: {str(e)}", "ERROR")
            raise e

    def run(self, path: str, nrows: Optional[int] = None, progress_callback=None):
        """Executes the full import lifecycle."""
        try:
            self.read(path, nrows, progress_callback)
            self.parse(progress_callback)
            self.normalize(progress_callback)
            return self.save(progress_callback)
        except Exception as e:
            self.log(f"Erro fatal no processamento: {str(e)}", "ERROR")
            import traceback
            traceback.print_exc()
            raise e
