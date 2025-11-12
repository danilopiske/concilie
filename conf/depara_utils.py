from typing import Dict, Any
from sqlalchemy.engine import Engine
from conf.funcoesbd import depara_listar


def gerar_mapeamento_depara(
    engine: Engine, contexto: str = "Rede", tipo_origem: str = "R"
) -> Dict[str, str]:
    """
    Retorna um dicionário {coluna_origem: coluna_destino} apenas para mapeamentos ativos do contexto e tipo especificados.
    """
    depara = depara_listar(engine, contexto=contexto, tipo_origem=tipo_origem)
    # Apenas ativos
    return {
        row["origem_nome"].strip(): row["destino_nome"].strip()
        for row in depara
        if row.get("ativo", 0) == 1
        and row.get("origem_nome")
        and row.get("destino_nome")
    }
