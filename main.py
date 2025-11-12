# main.py
import panel as pn
from datetime import datetime
import psutil
import socket
import sys

from conf.conf_bd import get_engine
from modules.ui_importacao import make_importacao_view
from modules.ui_gestao import make_gestao_view  # <-- IMPORTAÇÃO DA NOVA VIEW
from modules.reports import criar_interface_relatorio  # <-- IMPORTAÇÃO PARA RELATÓRIOS
from modules.ui_calculos import (
    make_calculos_view,
)  # <-- IMPORTAÇÃO DA INTERFACE DE CÁLCULOS
from proc.proc_usuarios import get_user_by_credentials
import logging

logging.basicConfig(level=logging.INFO)
# ---- Panel extension + notificações + Tabulator ----
try:
    pn.extension("tabulator", notifications=True, sizing_mode="stretch_width")
except Exception:
    try:
        pn.extension("tabulator")
    except Exception:
        pn.extension()


def _notify_success(msg: str):
    n = getattr(pn.state, "notifications", None)
    if n:
        try:
            n.success(msg)
        except Exception:
            pass


def _notify_error(msg: str):
    n = getattr(pn.state, "notifications", None)
    if n:
        try:
            n.error(msg)
        except Exception:
            pass


def _notify_warning(msg: str):
    n = getattr(pn.state, "notifications", None)
    if n:
        try:
            n.warning(msg)
        except Exception:
            pass


def _notify_info(msg: str):
    n = getattr(pn.state, "notifications", None)
    if n:
        try:
            n.info(msg)
        except Exception:
            pass


engine = get_engine()

# -------------------------
# Sessão (escopo por sessão)
# -------------------------
_session_user = {"value": None}


def get_session_user():
    return _session_user["value"]


def set_session_user(userdict):
    _session_user["value"] = userdict


def clear_session_user():
    _session_user["value"] = None


# -------------------------
# Sidebar / Navegação
# -------------------------
user_info_pane = pn.pane.Markdown("", sizing_mode="stretch_width")

menu_select = pn.widgets.Select(
    name="Função",
    options=[],  # preenchido após login
    value=None,
    sizing_mode="stretch_width",
)

btn_ir = pn.widgets.Button(name="Ir", button_type="primary")

# Área principal dinâmica
main_area = pn.Column(sizing_mode="stretch_both")


# -------------------------
# Views e Navegação
# -------------------------
def topbar(user):
    """Barra superior com info do usuário e logout."""
    lbl = pn.pane.Markdown(
        f"**{user.get('nome','')}** — {user.get('empresa','')}",
        sizing_mode="stretch_width",
    )
    btn_logout = pn.widgets.Button(name="Sair", button_type="warning", width=90)

    def _logout(_=None):
        clear_session_user()
        user_info_pane.object = ""
        menu_select.options = []
        menu_select.value = None
        # Volta para a tela de login
        main_area.clear()
        main_area.append(login_view())
        _notify_info("Sessão encerrada.")

    btn_logout.on_click(_logout)
    return pn.Row(lbl, btn_logout, sizing_mode="stretch_width")


def home_placeholder():
    return pn.Column(
        pn.pane.Markdown("### Bem-vindo(a) ao Concilie"),
        pn.pane.Markdown("Use o menu à esquerda para navegar."),
        sizing_mode="stretch_width",
    )


def render_view(route: str | None = None):
    """Despacha a rota selecionada para a view correspondente."""
    user = get_session_user()
    if not user:
        return login_view()

    if route == "Importar":
        return make_importacao_view(engine, usuario_logado=user.get("usuario"))

    if route == "Gestão":
        return make_gestao_view(engine, usuario_logado=user.get("usuario"))

    if route == "Cálculos":
        return make_calculos_view(engine)

    if route == "Relatórios":
        return criar_interface_relatorio(engine)

    # Fallback
    return pn.Column(
        pn.pane.Markdown(f"### {route or 'Função não definida'}"),
        pn.pane.Markdown("Conteúdo a implementar."),
        sizing_mode="stretch_width",
    )


def app_view(route: str | None = None):
    """Layout principal após login (topbar + conteúdo)."""
    user = get_session_user()
    content = render_view(route) if route else home_placeholder()
    return pn.Column(
        topbar(user),
        pn.layout.Divider(),
        content,
        sizing_mode="stretch_both",
        margin=(10, 15),
    )


def _go_to(route: str | None):
    """
    Troca segura do conteúdo principal.
    """
    route = (route or "").strip()
    try:
        main_area.clear()
        main_area.append(app_view(route))
    except Exception as e:
        main_area.clear()
        main_area.append(
            pn.Column(
                pn.pane.Markdown(f"### Erro ao abrir: `{route or '-'}`"),
                pn.pane.Markdown(f"```\n{e}\n```"),
                sizing_mode="stretch_width",
            )
        )


# -------------------------
# Login
# -------------------------
usuario_input = pn.widgets.TextInput(name="Usuário", placeholder="login")
senha_input = pn.widgets.PasswordInput(name="Senha", placeholder="senha")
btn_login = pn.widgets.Button(name="Entrar", button_type="primary")


def do_login(_=None):
    usuario = (usuario_input.value or "").strip()
    senha = senha_input.value
    if not usuario or not senha:
        _notify_error("Informe usuário e senha.")
        return

    user = get_user_by_credentials(engine, usuario, senha)
    if not user:
        _notify_error("Usuário ou senha inválidos.")
        return

    set_session_user(
        {
            "id": user["id"],
            "usuario": user["usuario"],
            "nome": user.get("nome") or user["usuario"],
            "empresa": user.get("empresa", ""),
            "grupo": user.get("grupo", ""),
            "funcao": user.get("funcao", ""),
            "login_time": datetime.now().isoformat(timespec="seconds"),
        }
    )

    user_info_pane.object = (
        f"**Usuário:** {user.get('nome') or user['usuario']}\n\n"
        f"**Função:** {user.get('funcao','') or '-'}"
    )

    menu_select.options = ["Importar", "Gestão", "Cálculos", "Relatórios"]
    menu_select.value = "Importar"
    _go_to("Importar")
    _notify_success(f"Bem-vindo, {user.get('nome') or user['usuario']}.")


btn_login.on_click(do_login)


def login_view():
    card = pn.Card(
        pn.pane.Markdown("### Login"),
        usuario_input,
        senha_input,
        btn_login,
        sizing_mode="fixed",
        width=380,
        height=380,
        header="Concilie",
    )
    return pn.Column(
        pn.Spacer(height=40),
        pn.Row(
            pn.Spacer(width=10),
            card,
            pn.Spacer(width=10),
            sizing_mode="stretch_width",
            align="center",
        ),
        sizing_mode="stretch_both",
    )


# -------------------------
# Navegar (sidebar)
# -------------------------
def on_navegar(_=None):
    user = get_session_user()
    if not user:
        main_area.clear()
        main_area.append(login_view())
        return
    if not menu_select.value:
        _notify_warning("Selecione uma função para navegar.")
        return
    _go_to(menu_select.value)


def _on_route_change(event):
    if event.new:
        _go_to(event.new)


menu_select.param.watch(_on_route_change, "value")
btn_ir.on_click(on_navegar)

# -------------------------
# Template
# -------------------------
template = pn.template.FastListTemplate(
    title="Concilie",
    sidebar=[
        pn.pane.Markdown("### Navegação"),
        user_info_pane,
        menu_select,
        # btn_ir,
    ],
    main=[main_area],
    sidebar_width=280,
    collapsed_sidebar=False,
)

# Primeira tela é o login
main_area.objects = [login_view()]
template.servable()


# -------------------------
# Servidor Panel
# -------------------------
def find_free_port(start_port=8500, max_attempts=10):
    import socket

    for port in range(start_port, start_port + max_attempts):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(("0.0.0.0", port))
                return port
        except OSError:
            continue
    raise OSError(
        f"Não foi possível encontrar uma porta livre entre {start_port} e {start_port + max_attempts-1}"
    )


if __name__ == "__main__":
    import sys
    import psutil

    # Mata processos Python anteriores que possam estar bloqueando as portas
    current_pid = psutil.Process().pid
    for proc in psutil.process_iter(["pid", "name"]):
        try:
            if proc.info["name"] == "python.exe" and proc.pid != current_pid:
                if any(
                    "panel" in conn.laddr.ip or conn.laddr.port in range(8500, 8600)
                    for conn in proc.connections()
                ):
                    proc.kill()
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass

    websocket_max_message_size = 200 * 1024 * 1024

    try:
        free_port = find_free_port(8500)
        print(f"\nIniciando servidor na porta {free_port}...")

        pn.serve(
            template,
            address="localhost",
            port=8500,
            # show=True,
            # autoreload=True,
            allow_websocket_origin=["*"],
            websocket_max_message_size=websocket_max_message_size,
        )
    except Exception as e:
        print(f"\nErro ao iniciar o servidor: {e}")
        print("\nPressione qualquer tecla para sair...")
        input()
        sys.exit(1)
    # ===== FIM DA CORREÇÃO =====
