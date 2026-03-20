from app.core.database import SessionLocal
from app.repositories.processamento_repository import ProcessamentoRepository
from app.schemas.processamento import ProcessamentoFilter
from app.services.cliente_service import ClienteService


def tool_listar_processamentos(limit: int = 5) -> str:
    """
    Lista os últimos processamentos de importação de arquivos (vendas, recebíveis) realizados no sistema.
    Útil para saber o que foi importado recentemente, datas e quantidades de linhas.
    """
    try:
        with SessionLocal() as db:
            repo = ProcessamentoRepository(db)
            # Buscar sem filtros complexos por enquanto, ordenar por data decrescente é o padrão do repo
            processamentos = repo.listar(limit=limit, simple=True)

            if not processamentos:
                return "Nenhum processamento encontrado."

            resultado = ["Últimos processamentos encontrados:"]
            for p in processamentos:
                resultado.append(
                    f"- ID: {p.id}\n"
                    f"  Arquivo: {p.nome_arquivo} ({p.tipo_arquivo})\n"
                    f"  Data: {p.data_inicio.strftime('%d/%m/%Y %H:%M') if p.data_inicio else 'N/A'}\n"
                    f"  Total Linhas: {p.linhas_total} (Sucesso: {p.linhas_sucesso}, Filtradas: {p.linhas_erro})"
                )

            return "\n\n".join(resultado)
    except Exception as e:
        return f"Erro ao listar processamentos: {str(e)}"

def tool_listar_clientes() -> str:
    """
    Lista os clientes cadastrados no sistema com seus IDs e CNPJs.
    Útil para mapear IDs de clientes para nomes.
    """
    try:
        with SessionLocal() as db:
            service = ClienteService(db)
            clientes = service.listar_clientes()

            if not clientes:
                return "Nenhum cliente cadastrado."

            resultado = ["Clientes cadastrados:"]
            for c in clientes:
                # Tenta acessar como dict ou objeto para garantir
                c_id = c.get('cliente_id') if isinstance(c, dict) else getattr(c, 'cliente_id', 'N/A')
                nome = c.get('nome_fantasia') if isinstance(c, dict) else getattr(c, 'nome_fantasia', 'N/A')
                cnpj = c.get('cnpj') if isinstance(c, dict) else getattr(c, 'cnpj', 'N/A')

                resultado.append(f"- ID: {c_id} | Nome: {nome} | CNPJ: {cnpj}")

            return "\n".join(resultado)
    except Exception as e:
        return f"Erro ao listar clientes: {str(e)}"
