# main.py
import panel as pn
from datetime import datetime

from conf.conf_bd import get_engine
from modules.ui_importacao import make_importacao_view
from proc.proc_usuarios import get_user_by_credentials

# ---- Panel extension + notificações + Tabulator ----
try:
    pn.extension('tabulator', notifications=True)
except Exception:
    try:
        pn.extension('tabulator')
    except Exception:
        pn.extension()


def _notify_success(msg: str):
    n = getattr(pn.state, "notifications", None)
    if n: 
        try: n.success(msg)
        except Exception: pass

def _notify_error(msg: str):
    n = getattr(pn.state, "notifications", None)
    if n: 
        try: n.error(msg)
        except Exception: pass

def _notify_warning(msg: str):
    n = getattr(pn.state, "notifications", None)
    if n: 
        try: n.warning(msg)
        except Exception: pass

def _notify_info(msg: str):
    n = getattr(pn.state, "notifications", None)
    if n: 
        try: n.info(msg)
        except Exception: pass

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
    options=[],      # preenchido após login
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
    Troca segura do conteúdo principal. Se alguma exceção ocorrer ao montar a view,
    mostra o erro no próprio main_area (evita página em branco).
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

    # Guarda sessão
    set_session_user({
        "id": user["id"],
        "usuario": user["usuario"],
        "nome": user.get("nome") or user["usuario"],
        "empresa": user.get("empresa", ""),
        "grupo": user.get("grupo", ""),
        "funcao": user.get("funcao", ""),
        "login_time": datetime.now().isoformat(timespec="seconds"),
    })

    # Sidebar
    user_info_pane.object = (
        f"**Usuário:** {user.get('nome') or user['usuario']}\n\n"
        f"**Função:** {user.get('funcao','') or '-'}"
    )

    # Menu inicial e navegação
    menu_select.options = ["Importar"]
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
        sizing_mode="fixed",   # mantém fixed
        width=380,
        height=260,            # <-- ADICIONE height para evitar W-1005
        header="Concilie",
    )
    return pn.Column(
        pn.Spacer(height=40),
        pn.Row(pn.Spacer(width=10), card, pn.Spacer(width=10), sizing_mode="stretch_width", align="center"),
        sizing_mode="stretch_both",
    )


# -------------------------
# Navegar (sidebar)
# -------------------------
def on_navegar(_=None):
    user = get_session_user()
    if not user:
        main_area.clear(); main_area.append(login_view()); return
    if not menu_select.value:
        _notify_warning("Selecione uma função para navegar."); return
    _go_to(menu_select.value)
def _on_route_change(event):
    if event.new:
        _go_to(event.new)
menu_select.param.watch(_on_route_change, "value")



btn_ir.on_click(on_navegar)

# Navegação automática ao trocar o select (dispensa clicar no botão)
def _on_route_change(event):
    # evita disparo no setup inicial quando value é None
    if event.new:
        _go_to(event.new)

menu_select.param.watch(_on_route_change, "value")

# -------------------------
# Template
# -------------------------
template = pn.template.FastListTemplate(
    title="Concilie",
    sidebar=[
        pn.pane.Markdown("### Navegação"),
        user_info_pane,
        menu_select,
        btn_ir,
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
if __name__ == "__main__":
    pn.serve(
        template,
        address="0.0.0.0",
        port=8501,
        show=False,
        autoreload=False,
        allow_websocket_origin=["*"],
    )
