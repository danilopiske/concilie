
import pandas as pd
from sqlalchemy.orm import Session
from fastapi import UploadFile, HTTPException
import shutil
import os
import uuid
import traceback
from pathlib import Path
from typing import List, Dict, Any, Optional
from app.core.config import settings

# Legacy logic imports
from proc.proc_importacao import (
    preparar_dataframe_de_arquivo,
    # normalizar functions are called internally by classificar_e_gravar
    classificar_e_gravar_vendas,
    classificar_e_gravar_recebiveis
)
from conf.funcoesbd import processamento_gerar_novo_id, processamento_salvar
from datetime import datetime

class ImportService:
    def __init__(self, db: Session):
        self.db = db
        # Ensure temp directory exists
        self.temp_dir = Path("temp_uploads")
        self.temp_dir.mkdir(exist_ok=True)

    async def preview_upload(
        self, 
        file: UploadFile, 
        cliente_id: int, 
        ec_id: str,
        contexto: str, 
        tipo: str,
        usuario: str
    ) -> Dict[str, Any]:
        """
        Step 1: Upload and Preview
        - Saves file to temp
        - Normalizes data
        - Returns preview rows and file_id (filename)
        """
        # 1. Save temp file with unique name
        filename = f"{uuid.uuid4()}_{file.filename}"
        temp_path = self.temp_dir / filename
        
        try:
            with temp_path.open("wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            
            # 2. Get Engine
            engine = self.db.get_bind()
            
            # 3. Parse and Normalize (No DB Save)
            def progress_cb(val): pass
            def log_cb(msg): pass

            try:
                # DEBUG: Trace Import Service Execution
                with open("debug_import_service.txt", "w") as f:
                    f.write(f"ImportService calling preparar_dataframe_de_arquivo at {datetime.now()}\n")
                    f.write(f"Path: {temp_path}\n")
                    f.write(f"Contexto: {contexto}\n")
                    f.write(f"Tipo: {tipo}\n")
            except:
                pass

            try:
                df_mapeado, transf, idx = preparar_dataframe_de_arquivo(
                    path=str(temp_path),
                    engine=engine,
                    contexto=contexto,
                    tipo_origem=tipo,
                    progress_callback=progress_cb,
                    log_callback=log_cb
                )
                
                # Normalize based on type
                if tipo == "R":
                     from proc.proc_importacao import normalizar_dataframe_recebiveis
                     df_norm = normalizar_dataframe_recebiveis(
                        df_mapeado, engine, ec_id, contexto, usuario
                     )
                else:
                    from proc.proc_importacao import normalizar_dataframe_vendas
                    # 'normalizar_dataframe_vendas' returns (processed, filtered), we combine for preview
                    df_proc, df_filt = normalizar_dataframe_vendas(
                        df_mapeado, engine, ec_id, contexto, usuario, tipo_arquivo=tipo
                    )
                    df_norm = pd.concat([df_proc, df_filt], ignore_index=True) if not df_filt.empty else df_proc

                # 4. Prepare Preview Data (First 50 rows)
                # Convert dates to string for JSON serialization
                preview_data = df_norm.head(50).fillna("").astype(str).to_dict(orient="records")
                
                return {
                    "file_id": filename,
                    "original_name": file.filename,
                    "total_lines": len(df_norm),
                    "preview": preview_data,
                    "columns": list(df_norm.columns)
                }

            except Exception as e:
                # If parsing fails, delete file and re-raise
                if temp_path.exists():
                    os.remove(temp_path)
                print(f"Error parsing file: {e}")
                traceback.print_exc()
                raise HTTPException(status_code=400, detail=f"Failed to parse file: {str(e)}")

        except Exception as e:
            if temp_path.exists() and not isinstance(e, HTTPException):
                try: os.remove(temp_path) 
                except: pass
            raise e

    async def confirm_import(
        self,
        file_id: str,
        cliente_id: int,
        ec_id: str,
        contexto: str,
        tipo: str,
        usuario: str,
        processamentoid: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Step 2: Confirm and Save
        - Reads existing temp file
        - Re-runs parsing/normalization (or we could cache DF, but file is safer/simpler for now)
        - Saves to DB
        - Deletes temp file
        """
        temp_path = self.temp_dir / file_id
        
        if not temp_path.exists():
            raise HTTPException(status_code=404, detail="File session expired or not found. Please upload again.")

        try:
            engine = self.db.get_bind()
            
            # Re-parse (Quick enough for most files, ensures clean state)
            def progress_cb(val): pass
            def log_cb(msg): pass
            
            df_mapeado, transf, idx = preparar_dataframe_de_arquivo(
                path=str(temp_path),
                engine=engine,
                contexto=contexto,
                tipo_origem=tipo,
                progress_callback=progress_cb,
                log_callback=log_cb
            )

            # Process and Save
            if tipo == "R":
                 # Recebiveis
                result_data = classificar_e_gravar_recebiveis(
                    engine=engine,
                    df=df_mapeado,
                    cliente_id=cliente_id,
                    ec_id=ec_id,
                    contexto=contexto,
                    usuario=usuario,
                    arquivo_origem=file_id, # Using file_id as origin name or need original name?
                    processamentoid=processamentoid
                )
            else: 
                # Vendas (V) or Lancamentos (L)
                result_data = classificar_e_gravar_vendas(
                    engine=engine,
                    df=df_mapeado,
                    cliente_id=cliente_id,
                    ec_id=ec_id,
                    contexto=contexto,
                    usuario=usuario,
                    arquivo_origem=file_id,
                    processamentoid=processamentoid
                )
                
            return {
                "status": "success",
                "message": "Data successfully saved to database",
                "data": result_data
            }

        except Exception as e:
            print(f"Error saving to DB: {e}")
            traceback.print_exc()
            raise HTTPException(status_code=500, detail=f"Failed to save data: {str(e)}")
            
        finally:
            # Always clean up file after confirmation attempt (success or failure)
            if temp_path.exists():
                try:
                    os.remove(temp_path)
                except Exception:
                    pass
