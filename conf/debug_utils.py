"""
Utilitário de Debug e Logging
Controla mensagens de debug de forma centralizada

Uso:
    from conf.debug_utils import debug_print, set_debug_mode, is_debug_enabled

    # Ativar/desativar debug
    set_debug_mode(True)  # Ou via variável de ambiente DEBUG=true

    # Usar em código
    debug_print("DEBUG", "Mensagem de debug")  # Só aparece se debug ativo
    debug_print("INFO", "Mensagem informativa")  # Sempre aparece
    debug_print("WARNING", "Aviso importante")  # Sempre aparece
    debug_print("ERROR", "Erro crítico")  # Sempre aparece
"""

import os
from datetime import datetime
from typing import Optional

# Estado global de debug
_debug_enabled = os.environ.get("DEBUG", "False").lower() in ("true", "1", "yes")
_verbose_enabled = os.environ.get("VERBOSE", "False").lower() in ("true", "1", "yes")


def set_debug_mode(enabled: bool):
    """
    Ativa ou desativa modo debug globalmente.

    Args:
        enabled: True para ativar, False para desativar
    """
    global _debug_enabled
    _debug_enabled = enabled


def set_verbose_mode(enabled: bool):
    """
    Ativa ou desativa modo verbose (mais detalhes).

    Args:
        enabled: True para ativar, False para desativar
    """
    global _verbose_enabled
    _verbose_enabled = enabled


def is_debug_enabled() -> bool:
    """Verifica se modo debug está ativo."""
    return _debug_enabled


def is_verbose_enabled() -> bool:
    """Verifica se modo verbose está ativo."""
    return _verbose_enabled


def debug_print(level: str, message: str, category: Optional[str] = None):
    """
    Imprime mensagem de debug/log com formatação.

    Args:
        level: Nível da mensagem (DEBUG, INFO, WARNING, ERROR)
        message: Mensagem a exibir
        category: Categoria/módulo opcional (ex: "REDE", "SQL", "IMPORT")

    Exemplos:
        debug_print("DEBUG", "Query executada", "SQL")
        debug_print("INFO", "Processamento concluído")
        debug_print("WARNING", "Valor nulo encontrado", "VALIDACAO")
    """
    level = level.upper()

    # Define se deve mostrar baseado no nível
    show_message = False

    if level in ("INFO", "WARNING", "ERROR"):
        # INFO, WARNING, ERROR sempre mostram
        show_message = True
    elif level == "DEBUG":
        # DEBUG só mostra se debug habilitado
        show_message = _debug_enabled
    elif level == "VERBOSE":
        # VERBOSE só mostra se verbose habilitado
        show_message = _verbose_enabled

    if not show_message:
        return

    # Formata timestamp
    timestamp = datetime.now().strftime("%H:%M:%S")

    # Formata categoria
    if category:
        prefix = f"[{timestamp}][{level}][{category}]"
    else:
        prefix = f"[{timestamp}][{level}]"

    # Define cor (se terminal suportar)
    colors = {
        "DEBUG": "\033[36m",  # Cyan
        "VERBOSE": "\033[90m",  # Gray
        "INFO": "\033[32m",  # Green
        "WARNING": "\033[33m",  # Yellow
        "ERROR": "\033[31m",  # Red
        "RESET": "\033[0m",
    }

    # Tenta usar cor, mas funciona mesmo sem suporte
    try:
        color = colors.get(level, "")
        reset = colors["RESET"]
        print(f"{color}{prefix}{reset} {message}")
    except:
        # Fallback sem cor
        print(f"{prefix} {message}")


def debug_timer(func_name: str, start_time: float):
    """
    Imprime tempo de execução de uma função.

    Args:
        func_name: Nome da função
        start_time: Timestamp de início (time.time())

    Exemplo:
        import time
        start = time.time()
        # ... código ...
        debug_timer("minha_funcao", start)
    """
    import time

    elapsed = time.time() - start_time
    debug_print("VERBOSE", f"{func_name}: {elapsed:.3f}s", "TIMER")


def debug_sql(sql: str, params: dict = None):
    """
    Imprime query SQL formatada para debug.

    Args:
        sql: Query SQL
        params: Parâmetros da query (opcional)
    """
    if not _debug_enabled:
        return

    debug_print("DEBUG", "SQL Query:", "SQL")

    # Formata SQL (indentação básica)
    formatted_sql = sql.strip()
    print(f"  {formatted_sql}")

    if params:
        print(f"  Params: {params}")


def debug_dataframe(df, name: str = "DataFrame", max_rows: int = 5):
    """
    Imprime informações sobre um DataFrame para debug.

    Args:
        df: pandas DataFrame
        name: Nome descritivo do DataFrame
        max_rows: Número máximo de linhas para mostrar
    """
    if not _debug_enabled:
        return

    debug_print("DEBUG", f"{name} Info:", "DATAFRAME")
    print(f"  Shape: {df.shape}")
    print(f"  Columns: {list(df.columns)}")
    print(f"  Memory: {df.memory_usage(deep=True).sum() / 1024 / 1024:.2f} MB")

    if len(df) > 0:
        print(f"\n  First {max_rows} rows:")
        print(df.head(max_rows).to_string(index=False))


# Funções de conveniência
def info(message: str, category: Optional[str] = None):
    """Mensagem informativa (sempre exibida)."""
    debug_print("INFO", message, category)


def warning(message: str, category: Optional[str] = None):
    """Mensagem de aviso (sempre exibida)."""
    debug_print("WARNING", message, category)


def error(message: str, category: Optional[str] = None):
    """Mensagem de erro (sempre exibida)."""
    debug_print("ERROR", message, category)


def debug(message: str, category: Optional[str] = None):
    """Mensagem de debug (só exibida se DEBUG=true)."""
    debug_print("DEBUG", message, category)


def verbose(message: str, category: Optional[str] = None):
    """Mensagem verbose (só exibida se VERBOSE=true)."""
    debug_print("VERBOSE", message, category)
