from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from typing import List, Optional
from app.core.database import get_db
from app.repositories.depara_repository import DeParaRepository
from app.schemas.depara import DeParaCreate, DeParaUpdate, DeParaResponse
import pandas as pd

router = APIRouter()

@router.get("/", response_model=List[DeParaResponse])
def listar_deparas(
    cliente_id: Optional[int] = None,
    contexto: Optional[str] = None,
    tipo_origem: Optional[str] = None,
    ativo: Optional[int] = 1,
    search: Optional[str] = None,
    db: Session = Depends(get_db)
):
    repo = DeParaRepository(db)
    return repo.listar(
        cliente_id=cliente_id,
        contexto=contexto,
        tipo_origem=tipo_origem,
        ativo=ativo,
        search=search
    )

@router.post("/", response_model=DeParaResponse)
def criar_depara(
    depara: DeParaCreate,
    db: Session = Depends(get_db)
):
    repo = DeParaRepository(db)
    return repo.criar(depara)

@router.put("/{id}", response_model=DeParaResponse)
def atualizar_depara(
    id: int,
    depara: DeParaUpdate,
    db: Session = Depends(get_db)
):
    repo = DeParaRepository(db)
    atualizado = repo.atualizar(id, depara)
    if not atualizado:
        raise HTTPException(status_code=404, detail="Configuração De-Para não encontrada")
    return atualizado

@router.delete("/{id}")
def deletar_depara(
    id: int,
    db: Session = Depends(get_db)
):
    repo = DeParaRepository(db)
    sucesso = repo.deletar(id)
    if not sucesso:
        raise HTTPException(status_code=404, detail="Configuração De-Para não encontrada")
    return {"message": "Deletado com sucesso"}

@router.post("/ler-cabecalhos")
async def ler_cabecalhos(
    file: UploadFile = File(...),
):
    """
    Lê os cabeçalhos de um arquivo (CSV ou Excel) para auxiliar no mapeamento.
    Usa a lógica LEGADA do proc_importacao para garantir paridade com o sistema desktop via Panel.
    """
    filename = file.filename.lower()
    temp_path = None
    
    try:
        import sys
        import os
        import tempfile
        import shutil
        from pathlib import Path
        
        # Adicionar raiz do projeto ao path para importar proc
        # Base: d:/Financial  base/Financial_P/apps/api/app/api/v1/endpoints/depara.py
        # Target: d:/Financial  base/Financial_P
        # Subindo 6 níveis a partir deste arquivo ou usando caminho absoluto fixo se necessário
        # Vamos tentar relativo primeiro para ser robusto
        current_dir = Path(__file__).resolve().parent
        project_root = current_dir.parent.parent.parent.parent.parent.parent
        sys.path.append(str(project_root))
        
        try:
            from proc.proc_importacao import safe_read_multisheet_file, read_file_with_header, is_multisheet_rede_file
        except ImportError:
            # Fallback para caminho hardcoded se a relatividade falhar (ambiente de dev vs prod)
            sys.path.append(r"d:/Financial  base/Financial_P")
            from proc.proc_importacao import safe_read_multisheet_file, read_file_with_header, is_multisheet_rede_file

        # Salvar arquivo temporário
        suffix = Path(filename).suffix
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            shutil.copyfileobj(file.file, tmp)
            temp_path = tmp.name
            
        # 1. Verificar se é multisheet Rede
        is_multisheet = is_multisheet_rede_file(temp_path)
        
        headers = []
        debug_info = {
            "filename": filename,
            "is_multisheet": is_multisheet,
            "legacy_mode": True
        }

        if is_multisheet:
            # Lógica Multisheet
            # Retorna dict: {sheet_name: {df, headers, ...}}
            result = safe_read_multisheet_file(temp_path)
            if result:
                # Pegar o primeiro sheet válido encontrado
                first_sheet_key = next(iter(result))
                headers = result[first_sheet_key].get('headers', [])
                debug_info['selected_sheet'] = first_sheet_key
                debug_info['all_sheets'] = list(result.keys())
        else:
            # Lógica Single Sheet
            # Retorna (df, idx_header, columns_list)
            _, idx, cols = read_file_with_header(temp_path)
            headers = cols
            debug_info['header_row_index'] = idx

        return {"headers": headers, "debug_info": debug_info}

    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Erro ao ler arquivo (Legacy Engine): {str(e)}")
    
    finally:
        # Limpar arquivo temporário
        if temp_path and os.path.exists(temp_path):
            try:
                os.unlink(temp_path)
            except:
                pass

def detectar_cabecalho(df: pd.DataFrame, max_scan: int = 100) -> tuple[int, int]:
    """
    Detecta a linha de cabeçalho usando heurística baseada em palavras-chave.
    Retorna (indice_linha, score).
    """
    # Palavras que indicam cabeçalho
    header_keywords = {
        # Financeiro
        "nsu", "bandeira", "autorização", "ec", "cnpj", "cpf", "valor", 
        "transação", "valor líquido", "valor bruto", "data da transação",
        "quantidade de parcelas", "taxa", "desconto", "liquido", "bruto",
        "pagamento", "recebimento",
        # Bancário
        "banco", "agencia", "conta", "codigo", "numero", "documento",
        # Identificação
        "nome", "cliente", "id", "lancamento", "recebivel", "venda",
        # Status e tipos
        "status", "situacao", "tipo", "modalidade", "parcela", "cartao",
        # Datas
        "data", "vencimento", "liquidacao", "processamento",
        # Rede / Adquirentes específicos
        "estabelecimento", "pv", "rv", "resumo de vendas", "comprovante", "terminal", "loja",
        "red", "rede", "cielo", "getnet", "stone", "bin", "safra", "pagseguro"
    }
    
    # Texto de resumo/relatório que deve ser EVITADO (Indicam que NÃO é a linha de cabeçalho principal)
    negative_keywords = [
        "período:", "data de emissão:", "usuário:", "página:", "filtros:", 
        "total", "subtotal", "a receber", "liquidado", "resumo financeiro",
        "extrato para simples conferência"
    ]

    best = (0, 0)  # (score, idx)

    # Limitar scan
    scan_limit = min(max_scan, len(df))
    
    for i in range(scan_limit):
        row = df.iloc[i]
        vals = row.astype(str).fillna("").str.strip()

        # Filtrar células não vazias
        non_empty_vals = [v for v in vals if v and v.lower() not in ["nan", "none"]]
        non_empty_count = len(non_empty_vals)

        if non_empty_count < 2:  # Muito poucas colunas preenchidas
            continue

        score = non_empty_count  # Base score

        # Bonus por palavras-chave
        header_text = " ".join(non_empty_vals).lower()
        
        # Penalizar linhas de resumo/relatório
        is_summary_line = False
        for neg in negative_keywords:
            if neg in header_text:
                score -= 10
                is_summary_line = True
                break
        
        if is_summary_line:
            continue

        keyword_matches = 0
        for keyword in header_keywords:
            if keyword in header_text:
                score += 3
                keyword_matches += 1

        if keyword_matches >= 3:
            score += 5
        elif keyword_matches >= 2:
            score += 2
            
        # Penalidade se parece com dados (números, datas)
        data_penalty = 0
        for val in non_empty_vals[:5]:
            val_clean = val.replace(",", "").replace(".", "").replace("/", "").replace("-", "")
            # Números longos
            if val_clean.isdigit() and len(val_clean) >= 4:
                data_penalty += 2
            # Datas
            elif "/" in val and len(val) >= 8:
                parts = val.split("/")
                if len(parts) == 3 and all(p.isdigit() for p in parts):
                    data_penalty += 2
        
        score -= data_penalty

        if score > best[0]:
            best = (score, i)

    return best[1], best[0]



@router.get("/colunas-sistema")
def listar_colunas_sistema(
    tipo: str = "V",
    db: Session = Depends(get_db)
):
    """
    Lista as colunas de destino do sistema baseadas no tipo (V=Venda, R=Recebível, L=Lançamento)
    """
    from sqlalchemy import text, inspect
    
    try:
        if tipo == "R":
            # Para Recebíveis, retorna colunas da tabela fisica
            inspector = inspect(db.get_bind())
            columns = [col["name"] for col in inspector.get_columns("recebiveis_processados")]
            return columns
        else:
            # Para Vendas/Lançamentos, retorna da tabela de controle
            # Busca apenas colunas mapeáveis da tabela depara_controle
            result = db.execute(text(
                "SELECT nome_coluna FROM depara_controle WHERE mapeavel = 'mapeavel' ORDER BY id"
            ))
            return [row[0] for row in result]
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao listar colunas do sistema: {str(e)}")

