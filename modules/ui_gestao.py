# modules/ui_gestao.py
from typing import Optional, List, Dict
import pandas as pd
import panel as pn
from sqlalchemy.engine import Engine
from datetime import datetime

from conf.funcoesbd import (
    clientes_listar,
    ecs_por_cliente,
    termos_listar,
    termo_adicionar,
    termo_excluir,
    fetch_all,
    bandeiras_por_ec,
    bandeiras_salvar_para_ec,
    bandeiras_disponiveis_listar,
    bandeira_disponivel_inserir,
    bandeira_disponivel_atualizar,
    bandeira_disponivel_deletar,
    cliente_detalhes_por_id,
    cliente_salvar,
    cliente_deletar,
    contextos_listar,
    taxas_por_ec,
    taxa_adicionar,
    taxa_excluir,
    taxas_copiar,
)


def _notify(kind: str, msg: str):
    n = getattr(pn.state, "notifications", None)
    if n:
        fn = getattr(n, kind, None)
        if fn:
            try:
                fn(msg)
            except Exception:
                pass


# =========================
# Componentes Comuns
# =========================


def _make_contexto_select(engine: Engine) -> pn.widgets.Select:
    """Cria um componente de seleção de contexto padronizado."""
    try:
        contextos = contextos_listar(engine)
        opts = ["padrao"] + [c["nome"] for c in contextos if c["nome"] != "padrao"]
    except Exception:
        opts = ["padrao"]

    return pn.widgets.Select(name="Contexto", options=opts, value="padrao", width=200)


# =========================
# ABA: CLIENTES
# =========================
def _make_tab_clientes(engine: Engine) -> pn.viewable.Viewable:

    # --- Widgets ---
    cliente_select = pn.widgets.Select(
        name="Selecione um Cliente para Editar ou Excluir", options=[], value=None
    )
    btn_novo_cliente = pn.widgets.Button(name="Novo Cliente", button_type="primary")

    cliente_id = pn.widgets.IntInput(
        name="Cliente ID (numérico)", value=0, disabled=False
    )
    nome_fantasia = pn.widgets.TextInput(name="Nome Fantasia")
    razao_social = pn.widgets.TextInput(name="Razão Social")
    cnpj = pn.widgets.TextInput(name="CNPJ")

    logradouro, numero, complemento = (
        pn.widgets.TextInput(name="Logradouro"),
        pn.widgets.TextInput(name="Número"),
        pn.widgets.TextInput(name="Complemento"),
    )
    bairro, cidade, uf_id = (
        pn.widgets.TextInput(name="Bairro"),
        pn.widgets.TextInput(name="Cidade"),
        pn.widgets.TextInput(name="UF", max_length=2),
    )

    telefone1, email1 = pn.widgets.TextInput(name="Telefone 1"), pn.widgets.TextInput(
        name="Email 1"
    )

    banco, agencia, conta = (
        pn.widgets.TextInput(name="Banco"),
        pn.widgets.TextInput(name="Agência"),
        pn.widgets.TextInput(name="Conta"),
    )

    ecs_input = pn.widgets.TextInput(
        name="ECs (separados por vírgula)", placeholder="Ex: 12345,67890"
    )

    btn_salvar = pn.widgets.Button(name="Salvar", button_type="success")
    btn_excluir = pn.widgets.Button(
        name="Excluir Cliente Selecionado", button_type="danger"
    )

    # --- Lógica ---
    def _get_opts_clientes():
        clientes = clientes_listar(engine)
        return {
            f"{c['cliente_id']} - {c.get('nome_fantasia')}": c["cliente_id"]
            for c in clientes
        }

    def _load_clientes(*events):
        try:
            cliente_select.options = list(_get_opts_clientes().keys())
        except Exception as e:
            _notify("error", f"Erro ao carregar clientes: {e}")
            cliente_select.options = []

    def _limpar_formulario(*events):
        cliente_select.value = None
        for widget in [
            nome_fantasia,
            razao_social,
            cnpj,
            logradouro,
            numero,
            complemento,
            bairro,
            cidade,
            uf_id,
            telefone1,
            email1,
            banco,
            agencia,
            conta,
            ecs_input,
        ]:
            widget.value = ""
        cliente_id.value = 0
        cliente_id.disabled = False

    def _preencher_formulario(*events):
        if not cliente_select.value:
            return

        try:
            opts = _get_opts_clientes()
            cid = opts.get(cliente_select.value)

            if not cid:
                return

            detalhes = cliente_detalhes_por_id(engine, cid)
            ecs = ecs_por_cliente(engine, cid)

            cliente_id.value = detalhes.get("cliente_id", 0)
            cliente_id.disabled = True
            nome_fantasia.value, razao_social.value, cnpj.value = (
                detalhes.get("nome_fantasia", ""),
                detalhes.get("razao_social", ""),
                detalhes.get("cnpj", ""),
            )
            logradouro.value, numero.value, complemento.value = (
                detalhes.get("logradouro", ""),
                detalhes.get("numero", ""),
                detalhes.get("complemento", ""),
            )
            bairro.value, cidade.value, uf_id.value = (
                detalhes.get("bairro", ""),
                detalhes.get("cidade", ""),
                detalhes.get("uf_id", ""),
            )
            telefone1.value, email1.value = detalhes.get("telefone1", ""), detalhes.get(
                "email1", ""
            )
            banco.value, agencia.value, conta.value = (
                detalhes.get("banco", ""),
                detalhes.get("agencia", ""),
                detalhes.get("conta", ""),
            )
            ecs_input.value = ", ".join(map(str, ecs))
        except Exception as e:
            _notify("error", f"Erro ao carregar detalhes: {e}")

    def salvar_action(*events):
        is_update = cliente_id.disabled
        cid = cliente_id.value

        if not cid or not nome_fantasia.value.strip():
            return _notify("warning", "Cliente ID e Nome Fantasia são obrigatórios.")

        dados = {
            "cliente_id": cid,
            "nome_fantasia": nome_fantasia.value,
            "razao_social": razao_social.value,
            "cnpj": cnpj.value,
            "endereco": {
                "logradouro": logradouro.value,
                "numero": numero.value,
                "complemento": complemento.value,
                "bairro": bairro.value,
                "cidade": cidade.value,
                "uf_id": uf_id.value.upper(),
            },
            "contatos": {"telefone1": telefone1.value, "email1": email1.value},
            "bancario": {
                "banco": banco.value,
                "agencia": agencia.value,
                "conta": conta.value,
            },
            "ecs": [ec.strip() for ec in ecs_input.value.split(",") if ec.strip()],
        }

        try:
            cliente_salvar(engine, dados, is_update=is_update)
            _notify("success", f"Cliente '{nome_fantasia.value}' salvo!")
            _limpar_formulario()
            _load_clientes()
        except Exception as e:
            _notify("error", f"Erro ao salvar: {e}")

    def excluir_action(*events):
        if not cliente_select.value:
            return _notify("warning", "Selecione um cliente para excluir.")

        try:
            opts = _get_opts_clientes()
            cid = opts.get(cliente_select.value)
            cliente_deletar(engine, cid)
            _notify("success", "Cliente excluído.")
            _limpar_formulario()
            _load_clientes()
        except Exception as e:
            _notify("error", f"Erro ao excluir: {e}")

    # --- Associações e Carga Inicial ---
    cliente_select.param.watch(_preencher_formulario, "value")
    btn_novo_cliente.on_click(_limpar_formulario)
    btn_salvar.on_click(salvar_action)
    btn_excluir.on_click(excluir_action)
    _load_clientes()

    return pn.Column(
        pn.pane.Markdown("### Gestão de Clientes"),
        pn.Row(cliente_select, btn_novo_cliente, btn_excluir),
        pn.layout.Divider(),
        pn.pane.Markdown("#### Dados Cadastrais"),
        pn.Row(cliente_id, nome_fantasia, razao_social, cnpj),
        pn.pane.Markdown("#### Endereço"),
        pn.Row(logradouro, numero, complemento),
        pn.Row(bairro, cidade, uf_id),
        pn.pane.Markdown("#### Contato Principal"),
        pn.Row(telefone1, email1),
        pn.pane.Markdown("#### Dados Bancários"),
        pn.Row(banco, agencia, conta),
        pn.pane.Markdown("#### Estabelecimentos (ECs)"),
        ecs_input,
        pn.layout.Divider(),
        btn_salvar,
        sizing_mode="stretch_width",
    )


# =========================
# ABA: TERMOS FILTRÁVEIS
# =========================
def _make_tab_termos_filtraveis(engine: Engine) -> pn.viewable.Viewable:
    try:
        _clientes = clientes_listar(engine)
        clientes_opts = {
            f"{c['cliente_id']} - {c.get('nome_fantasia')}": c["cliente_id"]
            for c in _clientes
        }
    except Exception:
        clientes_opts = {}

    # Seletores principais
    cliente_select = pn.widgets.Select(
        name="Cliente",
        options=list(clientes_opts.keys()),
        value=(list(clientes_opts.keys())[0] if clientes_opts else None),
    )
    ec_select = pn.widgets.Select(name="EC", options=[])
    contexto_select = _make_contexto_select(engine)

    termo_input = pn.widgets.TextInput(
        name="Novo Termo para Filtrar", placeholder="Ex: CANCELADO"
    )
    tipo_input = pn.widgets.Select(
        name="Tipo do Termo",
        options=[
            ("Venda/Lançamento", "v"),
            ("Recebíveis", "r"),
            ("Lançamento (apenas)", "l"),
            ("Status (filtrar por status)", "status"),
        ],
        value="v",
        width=180,
    )
    btn_adicionar = pn.widgets.Button(name="Adicionar Termo", button_type="primary")

    grid = pn.widgets.Tabulator(
        pd.DataFrame(columns=["id", "ec", "termo", "tipo"]),
        height=400,
        show_index=False,
        sizing_mode="stretch_width",
        selectable="checkbox",
        pagination="local",
        page_size=15,
    )
    btn_excluir = pn.widgets.Button(
        name="Excluir Termo Selecionado", button_type="danger", disabled=True
    )
    btn_atualizar = pn.widgets.Button(name="Atualizar Lista", button_type="primary")

    def _load_ecs(*events):
        cliente_selecionado = cliente_select.value
        if cliente_selecionado and cliente_selecionado in clientes_opts:
            cliente_id = clientes_opts[cliente_selecionado]
            try:
                ecs = ecs_por_cliente(engine, cliente_id)
                ec_select.options = [str(ec) for ec in ecs]
            except Exception:
                ec_select.options = []
        else:
            ec_select.options = []

        if ec_select.options:
            ec_select.value = ec_select.options[0]
        else:
            ec_select.value = None
        _load_grid_termos()

    def _load_grid_termos(*events):
        ec = ec_select.value
        contexto = contexto_select.value if contexto_select.value else "padrao"
        if not ec:
            grid.value = pd.DataFrame(columns=["id", "ec", "termo"])
            return

        try:
            termos_dicts = fetch_all(
                engine,
                "SELECT id, ec, termo, tipo FROM termos_filtraveis WHERE ec = :ec AND contexto = :contexto ORDER BY termo",
                {"ec": str(ec), "contexto": contexto},
            )
            grid.value = pd.DataFrame(termos_dicts if termos_dicts else [])
        except Exception as e:
            _notify("error", f"Erro ao carregar grid de termos: {e}")

        grid.selection = []
        btn_excluir.disabled = True

    def on_selection(event):
        btn_excluir.disabled = not event.new

    def adicionar_termo_action(event):
        ec = ec_select.value
        termo = termo_input.value.strip()
        tipo = (
            tipo_input.value[1]
            if isinstance(tipo_input.value, tuple)
            else tipo_input.value
        )
        contexto = contexto_select.value if contexto_select.value else "padrao"
        if not ec or not termo:
            return _notify(
                "warning", "Selecione um EC e digite um termo para adicionar."
            )
        try:
            termo_adicionar(engine, str(ec), termo, contexto, tipo)
            _notify(
                "success",
                f"Termo '{termo}' (tipo {tipo}) adicionado ao EC {ec} no contexto '{contexto}'.",
            )
            termo_input.value = ""
            _load_grid_termos()
        except Exception as e:
            _notify("error", f"Falha ao adicionar termo: {e}")

    def excluir_termo_action(event):
        contexto = contexto_select.value if contexto_select.value else "padrao"
        if grid.selection:
            try:
                for idx in grid.selection:
                    termo = grid.value.iloc[idx]["termo"]
                    termo_excluir(
                        engine,
                        str(grid.value.iloc[idx]["ec"]),
                        str(termo).strip().lower(),
                        contexto,
                    )
                _notify(
                    "success",
                    f"{len(grid.selection)} termo(s) excluído(s) do contexto '{contexto}'.",
                )
                _load_grid_termos()
            except Exception as e:
                _notify("error", f"Falha ao excluir: {e}")

    cliente_select.param.watch(_load_ecs, "value")
    ec_select.param.watch(_load_grid_termos, "value")
    contexto_select.param.watch(_load_grid_termos, "value")

    btn_adicionar.on_click(adicionar_termo_action)
    grid.param.watch(on_selection, "selection")
    btn_excluir.on_click(excluir_termo_action)
    btn_atualizar.on_click(_load_grid_termos)
    _load_ecs()

    return pn.Column(
        pn.pane.Markdown("### Gestão de Termos Filtráveis"),
        pn.pane.Markdown(
            "Os termos cadastrados aqui (ex: 'cancelado') serão usados para mover transações para a tabela `vendas_filtradas` ou `recebiveis_filtrados`, conforme o tipo.\n\nTipo 'v': usado para vendas e lançamentos.\nTipo 'r': usado para recebíveis.\nTipo 'l': usado apenas para lançamentos (casos especiais)."
        ),
        pn.Row(cliente_select, ec_select, contexto_select, btn_atualizar),
        pn.layout.Divider(),
        pn.Row(
            pn.Column(
                "#### Adicionar Novo Termo",
                termo_input,
                tipo_input,
                btn_adicionar,
                width=350,
            ),
            pn.Column("#### Gerenciar Termos Existentes", grid, btn_excluir),
        ),
        sizing_mode="stretch_width",
    )


# =========================
# ABA: BANDEIRAS (CADASTRO GERAL)
# =========================
def _make_tab_bandeiras_cadastro(engine: Engine) -> pn.viewable.Viewable:
    """Aba para gerenciar bandeiras na tabela mestre bandeiras_disponiveis"""
    grid = pn.widgets.Tabulator(
        pd.DataFrame(columns=["nome", "padrao"]),
        height=400,
        show_index=False,
        sizing_mode="stretch_width",
        selectable="checkbox",
        pagination="local",
        page_size=20,
    )

    nome_input = pn.widgets.TextInput(name="Nome da Bandeira", placeholder="Ex: VISA")
    padrao_checkbox = pn.widgets.Checkbox(
        name="Padrão (ativada por padrão para novos ECs)", value=False
    )

    btn_novo = pn.widgets.Button(name="Novo", button_type="light")
    btn_salvar = pn.widgets.Button(name="Salvar", button_type="success")
    btn_excluir = pn.widgets.Button(name="Excluir", button_type="danger", disabled=True)
    btn_atualizar = pn.widgets.Button(name="🔄 Atualizar Lista", button_type="primary")

    nome_selecionado = [None]  # Usar lista para permitir modificação em closures

    def _load_grid(*events):
        try:
            bandeiras = bandeiras_disponiveis_listar(engine)
            df = pd.DataFrame(bandeiras)
            if not df.empty:
                df["padrao"] = df["padrao"].astype(int)
            grid.value = (
                df if not df.empty else pd.DataFrame(columns=["nome", "padrao"])
            )
            grid.selection = []
            btn_excluir.disabled = True
        except Exception as e:
            _notify("error", f"Erro ao carregar bandeiras: {e}")

    def _limpar_formulario(*events):
        nome_input.value = ""
        padrao_checkbox.value = False
        nome_selecionado[0] = None
        btn_excluir.disabled = True
        grid.selection = []

    def _preencher_formulario(selected_rows):
        if not selected_rows:
            _limpar_formulario()
            return

        row = grid.value.iloc[selected_rows[0]]
        nome_selecionado[0] = row["nome"]
        nome_input.value = row["nome"]
        padrao_checkbox.value = bool(row.get("padrao", 0))
        btn_excluir.disabled = False

    def _salvar(*events):
        nome = (nome_input.value or "").strip().upper()
        if not nome:
            return _notify("warning", "Nome da bandeira é obrigatório.")

        try:
            if nome_selecionado[0]:
                # Atualizar
                if bandeira_disponivel_atualizar(
                    engine, nome_selecionado[0], nome, 1 if padrao_checkbox.value else 0
                ):
                    _notify("success", f"Bandeira '{nome}' atualizada com sucesso.")
                else:
                    _notify("error", "Erro ao atualizar bandeira.")
            else:
                # Inserir
                if bandeira_disponivel_inserir(
                    engine, nome, 1 if padrao_checkbox.value else 0
                ):
                    _notify("success", f"Bandeira '{nome}' criada com sucesso.")
                else:
                    _notify("error", "Erro ao criar bandeira. Verifique se já existe.")

            _load_grid()
            _limpar_formulario()
        except Exception as e:
            _notify("error", f"Erro ao salvar: {e}")

    def _excluir(*events):
        if not nome_selecionado[0]:
            return

        try:
            if bandeira_disponivel_deletar(engine, nome_selecionado[0]):
                _notify(
                    "success", f"Bandeira '{nome_selecionado[0]}' excluída com sucesso."
                )
                _load_grid()
                _limpar_formulario()
            else:
                _notify("error", "Erro ao excluir bandeira.")
        except Exception as e:
            _notify("error", f"Erro ao excluir: {e}")

    grid.param.watch(lambda e: _preencher_formulario(e.new), "selection")
    btn_novo.on_click(_limpar_formulario)
    btn_salvar.on_click(_salvar)
    btn_excluir.on_click(_excluir)
    btn_atualizar.on_click(_load_grid)

    _load_grid()

    return pn.Column(
        pn.pane.Markdown("### Gestão de Bandeiras (Cadastro Geral)"),
        pn.pane.Markdown(
            "Gerencie as bandeiras disponíveis no sistema. Estas bandeiras podem ser configuradas por EC na aba 'Bandeiras por EC'."
        ),
        pn.Row(btn_atualizar, sizing_mode="stretch_width"),
        grid,
        pn.layout.Divider(),
        pn.pane.Markdown("#### Formulário de Bandeira"),
        pn.Row(nome_input, padrao_checkbox, sizing_mode="stretch_width"),
        pn.Row(btn_novo, btn_salvar, btn_excluir, sizing_mode="stretch_width"),
        sizing_mode="stretch_width",
    )


# =========================
# ABA: BANDEIRAS POR EC
# =========================
def _make_tab_bandeiras(engine: Engine) -> pn.viewable.Viewable:
    checkboxes_bandeiras = {}
    try:
        _clientes = clientes_listar(engine)
        clientes_opts = {
            f"{c['cliente_id']} - {c.get('nome_fantasia')}": c["cliente_id"]
            for c in _clientes
        }
    except Exception:
        clientes_opts = {}

    cliente_select = pn.widgets.Select(
        name="Cliente",
        options=list(clientes_opts.keys()),
        value=(list(clientes_opts.keys())[0] if clientes_opts else None),
    )
    ec_select = pn.widgets.Select(name="EC", options=[])

    bandeiras_container = pn.FlexBox(sizing_mode="stretch_width")
    btn_salvar = pn.widgets.Button(name="Salvar Bandeiras", button_type="primary")

    def _load_ecs(*events):
        cliente_selecionado = cliente_select.value
        if cliente_selecionado and cliente_selecionado in clientes_opts:
            cliente_id = clientes_opts[cliente_selecionado]
            try:
                ecs = ecs_por_cliente(engine, cliente_id)
                ec_select.options = [str(ec) for ec in ecs]
            except Exception:
                ec_select.options = []
        else:
            ec_select.options = []

        if ec_select.options:
            ec_select.value = ec_select.options[0]
        else:
            ec_select.value = None

    def _load_bandeiras(*events):
        nonlocal checkboxes_bandeiras
        checkboxes_bandeiras.clear()
        bandeiras_container.clear()
        ec = ec_select.value
        if not ec:
            bandeiras_container.append(
                pn.pane.Markdown("Selecione um EC para configurar as bandeiras.")
            )
            return

        bandeiras_mestras = bandeiras_disponiveis_listar(engine)
        if not bandeiras_mestras:
            _notify(
                "error",
                "Nenhuma bandeira encontrada na tabela `bandeiras_disponiveis`.",
            )
            return

        config_ec = bandeiras_por_ec(engine, str(ec))

        lista_checkboxes = []
        for bandeira_info in bandeiras_mestras:
            nome_bandeira = bandeira_info["nome"]
            valor_atual = config_ec.get(
                nome_bandeira, bandeira_info.get("padrao", False)
            )

            cb = pn.widgets.Checkbox(name=nome_bandeira, value=bool(valor_atual))
            checkboxes_bandeiras[nome_bandeira] = cb
            lista_checkboxes.append(cb)

        bandeiras_container.objects = lista_checkboxes

    def salvar_action(event):
        ec = ec_select.value
        if not ec:
            return _notify("warning", "Nenhum EC selecionado.")

        config_para_salvar = {
            nome: 1 if cb.value else 0 for nome, cb in checkboxes_bandeiras.items()
        }

        try:
            bandeiras_salvar_para_ec(engine, str(ec), config_para_salvar)
            _notify("success", f"Configuração de bandeiras para o EC {ec} foi salva.")
        except Exception as e:
            _notify("error", f"Erro ao salvar bandeiras: {e}")

    cliente_select.param.watch(_load_ecs, "value")
    ec_select.param.watch(_load_bandeiras, "value")
    btn_salvar.on_click(salvar_action)

    _load_ecs()

    return pn.Column(
        pn.pane.Markdown("### Gestão de Bandeiras por EC"),
        pn.pane.Markdown(
            "Selecione as bandeiras que devem ser consideradas válidas para um EC. Transações de bandeiras não selecionadas serão movidas para `vendas_filtradas`."
        ),
        pn.Row(cliente_select, ec_select),
        pn.layout.Divider(),
        pn.pane.Markdown("#### Bandeiras Disponíveis"),
        bandeiras_container,
        pn.layout.Divider(),
        btn_salvar,
        sizing_mode="stretch_width",
    )


# =========================
# ABA: TAXAS POR EC
# =========================
def _make_tab_taxas(engine: Engine) -> pn.viewable.Viewable:
    # --- Seletores ---
    try:
        _clientes = clientes_listar(engine)
        clientes_opts = {
            f"{c['cliente_id']} - {c.get('nome_fantasia')}": c["cliente_id"]
            for c in _clientes
        }
    except Exception:
        clientes_opts = {}

    cliente_select = pn.widgets.Select(
        name="Cliente",
        options=list(clientes_opts.keys()),
        value=(list(clientes_opts.keys())[0] if clientes_opts else None),
    )
    ec_select = pn.widgets.Select(name="EC", options=[])
    contexto_select = _make_contexto_select(engine)

    # --- Widgets do Formulário de Inserção ---
    taxa_generica_checkbox = pn.widgets.Checkbox(
        name="Taxa Genérica (todas as bandeiras)",
        value=False,
        width=300,
        styles={
            "fontWeight": "bold",
            "fontSize": "14px",
            "color": "#1976d2",
        },
    )
    bandeira_input = pn.widgets.TextInput(name="Bandeira", placeholder="Ex: Visa")
    forma_pgto_input = pn.widgets.TextInput(
        name="Forma de Pagamento", placeholder="Ex: CREDITO A VISTA"
    )
    parcelado_select = pn.widgets.RadioButtonGroup(
        name="Parcelado",
        options={"Não": "N", "Sim": "S"},
        button_type="success",
        orientation="horizontal",
        value="N",
        width=180,
    )
    taxa_input = pn.widgets.FloatInput(name="Taxa (%)", value=0.0, step=0.01)
    p_ini_input = pn.widgets.IntInput(name="Parcela Inicial", value=1, step=1, start=1)
    p_fim_input = pn.widgets.IntInput(name="Parcela Final", value=1, step=1, start=1)
    data_ini_input = pn.widgets.DatePicker(
        name="Data de Início", value=datetime.now().date()
    )
    data_fim_input = pn.widgets.DatePicker(name="Data de Fim")
    btn_inserir = pn.widgets.Button(name="Inserir Taxa", button_type="primary")

    # --- Widgets para Deletar ---
    taxas_select = pn.widgets.Select(
        name="Selecione a Taxa para Deletar", options={}, height=80
    )
    btn_deletar = pn.widgets.Button(
        name="Deletar Taxa Selecionada", button_type="danger"
    )

    # --- Grid de Visualização ---
    grid_taxas = pn.widgets.Tabulator(
        pd.DataFrame(),
        layout="fit_data",
        sizing_mode="stretch_width",
        show_index=False,
        header_filters=True,
        pagination="local",
        page_size=10,
    )

    # --- Lógica de Carregamento ---
    def _load_ecs(*events):
        cliente_selecionado = cliente_select.value
        if cliente_selecionado in clientes_opts:
            cliente_id = clientes_opts[cliente_selecionado]
            ec_select.options = [str(ec) for ec in ecs_por_cliente(engine, cliente_id)]
        else:
            ec_select.options = []
        ec_select.value = ec_select.options[0] if ec_select.options else None

    def _load_taxas(*events):
        ec = ec_select.value
        if not ec:
            grid_taxas.value = pd.DataFrame()
            taxas_select.options = {}
            return

        contexto = contexto_select.value if contexto_select.value else "padrao"
        taxas = taxas_por_ec(engine, str(ec), contexto)
        df_taxas = pd.DataFrame(taxas)
        if not df_taxas.empty and "taxa" in df_taxas.columns:
            df_taxas["taxa"] = df_taxas["taxa"].astype(float)
        grid_taxas.value = df_taxas
        opcoes_delete = {
            f"{row['id']} | {row['bandeira']} | {row['forma_pagamento']} | {row['taxa']}%": row[
                "id"
            ]
            for index, row in df_taxas.iterrows()
        }
        taxas_select.options = opcoes_delete
        taxas_select.value = None

    # --- Ações dos Botões ---
    def on_taxa_generica_change(event):
        """Desabilita/habilita campo bandeira conforme checkbox"""
        if event.new:
            bandeira_input.disabled = True
            bandeira_input.value = ""  # Limpar valor
        else:
            bandeira_input.disabled = False

    taxa_generica_checkbox.param.watch(on_taxa_generica_change, "value")

    def on_inserir(_=None):
        # Validação: se taxa genérica, não precisa de bandeira
        if taxa_generica_checkbox.value:
            if not all(
                [
                    ec_select.value,
                    forma_pgto_input.value,
                    taxa_input.value > 0,
                ]
            ):
                return _notify("warning", "Preencha EC, Forma de Pagamento e Taxa.")
        else:
            if not all(
                [
                    ec_select.value,
                    bandeira_input.value,
                    forma_pgto_input.value,
                    taxa_input.value > 0,
                ]
            ):
                return _notify(
                    "warning", "Preencha os campos obrigatórios para inserir."
                )

        try:
            # Se taxa genérica, bandeira = NULL (enviar None ou string vazia)
            bandeira_valor = (
                None if taxa_generica_checkbox.value else bandeira_input.value.strip()
            )

            taxa_adicionar(
                engine,
                {
                    "ec": ec_select.value,
                    "bandeira": bandeira_valor,
                    "forma_pagamento": forma_pgto_input.value.strip(),
                    "parcelado": parcelado_select.value,
                    "parcelas_ini": p_ini_input.value,
                    "parcelas_fim": p_fim_input.value,
                    "data_ini": data_ini_input.value,
                    "data_fim": data_fim_input.value,
                    "taxa": taxa_input.value,
                },
                contexto=contexto_select.value if contexto_select.value else "padrao",
            )
            tipo_taxa = (
                "genérica (todas bandeiras)"
                if taxa_generica_checkbox.value
                else "específica"
            )
            _notify("success", f"Taxa {tipo_taxa} inserida!")
            _load_taxas()
        except Exception as e:
            _notify("error", f"Erro ao inserir taxa: {e}")

    def on_deletar(_=None):
        taxa_id = taxas_select.value
        if not taxa_id:
            return _notify("warning", "Selecione uma taxa na lista para deletar.")
        try:
            taxa_excluir(engine, int(taxa_id))
            _notify("success", "Taxa deletada!")
            _load_taxas()
        except Exception as e:
            _notify("error", f"Erro ao deletar taxa: {e}")

    # --- Vinculando Eventos ---
    cliente_select.param.watch(_load_ecs, "value")
    ec_select.param.watch(_load_taxas, "value")
    contexto_select.param.watch(_load_taxas, "value")
    btn_inserir.on_click(on_inserir)
    btn_deletar.on_click(on_deletar)

    # --- Carga Inicial ---
    _load_ecs()

    # --- Layout da View ---
    form_inserir = pn.Card(
        pn.Column(
            taxa_generica_checkbox,
            pn.Row(
                pn.Column(
                    bandeira_input,
                    forma_pgto_input,
                    parcelado_select,
                    sizing_mode="fixed",
                    width=260,
                ),
                pn.Column(
                    p_ini_input, p_fim_input, taxa_input, sizing_mode="fixed", width=220
                ),
                pn.Column(
                    data_ini_input, data_fim_input, sizing_mode="fixed", width=220
                ),
                pn.Column(btn_inserir, sizing_mode="fixed", width=180, align="end"),
                sizing_mode="stretch_width",
                align="center",
                margin=(10, 0, 10, 0),
            ),
        ),
        title="➕ Adicionar Nova Taxa",
        sizing_mode="stretch_width",
        min_width=900,
    )
    form_deletar = pn.Card(
        pn.Row(
            pn.Column(taxas_select, sizing_mode="fixed", width=400),
            pn.Column(btn_deletar, sizing_mode="fixed", width=180, align="end"),
            sizing_mode="stretch_width",
            align="center",
            margin=(10, 0, 10, 0),
        ),
        title="🗑️ Deletar Taxa Existente",
        sizing_mode="stretch_width",
        min_width=600,
    )

    # --- Widgets para Copiar Taxas ---
    ec_origem_select = pn.widgets.Select(name="EC de Origem", options=[], width=200)
    ecs_destino_selector = pn.widgets.MultiChoice(
        name="ECs de Destino (selecione um ou mais)", options=[], height=120, width=400
    )
    sobrescrever_checkbox = pn.widgets.Checkbox(
        name="Sobrescrever taxas existentes nos ECs de destino", value=False, width=400
    )
    btn_copiar = pn.widgets.Button(
        name="Copiar Taxas", button_type="success", width=150
    )
    resultado_copia_text = pn.pane.Markdown("", height=80)

    # --- Lógica de Cópia ---
    def _load_ecs_copiar(*events):
        """Carrega a lista de todos os ECs disponíveis para copiar taxas."""
        try:
            _clientes = clientes_listar(engine)
            todos_ecs = []
            for cliente in _clientes:
                ecs = ecs_por_cliente(engine, cliente["cliente_id"])
                todos_ecs.extend([str(ec) for ec in ecs])

            # Remove duplicatas e ordena
            todos_ecs = sorted(list(set(todos_ecs)))

            ec_origem_select.options = todos_ecs
            ecs_destino_selector.options = todos_ecs

            # Limpa seleção anterior
            if todos_ecs:
                ec_origem_select.value = todos_ecs[0]
            ecs_destino_selector.value = []

        except Exception as e:
            _notify("error", f"Erro ao carregar ECs: {e}")

    def on_copiar(event):
        """Executa a cópia de taxas entre ECs."""
        ec_origem = ec_origem_select.value
        ecs_destino = ecs_destino_selector.value
        sobrescrever = sobrescrever_checkbox.value
        contexto = contexto_select.value

        # Validações
        if not ec_origem:
            _notify("warning", "Selecione um EC de origem.")
            return

        if not ecs_destino:
            _notify("warning", "Selecione pelo menos um EC de destino.")
            return

        try:
            # Executa a cópia
            resultado = taxas_copiar(
                engine, ec_origem, ecs_destino, contexto, sobrescrever
            )

            # Exibe resultado
            msg_parts = []
            if resultado["copiadas"] > 0:
                msg_parts.append(
                    f"✅ **{resultado['copiadas']} taxas copiadas com sucesso!**"
                )

            if resultado["removidas"] > 0:
                msg_parts.append(
                    f"🗑️ {resultado['removidas']} taxas removidas (sobrescrever ativado)"
                )

            if resultado["erros"]:
                msg_parts.append(f"⚠️ **Erros encontrados:**")
                for erro in resultado["erros"][:5]:  # Limita a 5 erros
                    msg_parts.append(f"- {erro}")
                if len(resultado["erros"]) > 5:
                    msg_parts.append(
                        f"- ... e mais {len(resultado['erros']) - 5} erros"
                    )

            resultado_copia_text.object = (
                "\n\n".join(msg_parts) if msg_parts else "Nenhuma operação realizada."
            )

            # Notificação
            if resultado["copiadas"] > 0 and not resultado["erros"]:
                _notify(
                    "success",
                    f"{resultado['copiadas']} taxas copiadas de {ec_origem} para {len(ecs_destino)} EC(s)",
                )
            elif resultado["erros"]:
                _notify(
                    "warning", f"Cópia concluída com {len(resultado['erros'])} erro(s)"
                )
            else:
                _notify("info", "Nenhuma taxa foi copiada")

            # Recarrega a grid se estiver visualizando um dos ECs afetados
            if ec_select.value in ecs_destino or ec_select.value == ec_origem:
                _load_taxas()

        except Exception as e:
            _notify("error", f"Erro ao copiar taxas: {e}")
            resultado_copia_text.object = f"❌ **Erro:** {str(e)}"

    # Vincula eventos
    btn_copiar.on_click(on_copiar)

    # Carrega ECs ao trocar de contexto
    contexto_select.param.watch(_load_ecs_copiar, "value")

    form_copiar = pn.Card(
        pn.Column(
            pn.pane.Markdown(
                "Copie todas as taxas de um EC para outros ECs. "
                "Útil para replicar configurações entre estabelecimentos."
            ),
            pn.Row(
                pn.Column(ec_origem_select, sizing_mode="fixed", width=220),
                pn.Column(ecs_destino_selector, sizing_mode="fixed", width=420),
                sizing_mode="stretch_width",
            ),
            sobrescrever_checkbox,
            pn.Row(btn_copiar, align="start"),
            resultado_copia_text,
            sizing_mode="stretch_width",
        ),
        title="📋 Copiar Taxas entre ECs",
        sizing_mode="stretch_width",
        min_width=700,
        collapsed=True,
    )

    # Carga inicial dos ECs para copiar
    _load_ecs_copiar()

    return pn.Column(
        pn.pane.Markdown("### Gestão de Taxas por EC"),
        pn.Row(cliente_select, ec_select, contexto_select),
        pn.layout.Divider(),
        form_inserir,
        form_deletar,
        form_copiar,
        pn.layout.Divider(),
        pn.pane.Markdown("#### Taxas Cadastradas para o EC/Contexto Selecionado"),
        grid_taxas,
        sizing_mode="stretch_width",
    )


# =========================
# ABA: CONTEXTOS
# =========================
def _make_tab_contextos(engine: Engine) -> pn.viewable.Viewable:
    # Grid para listar contextos
    grid = pn.widgets.Tabulator(
        pd.DataFrame(
            columns=[
                "id",
                "nome",
                "descricao",
                "ativo",
                "criado_por",
                "criado_em",
                "atualizado_em",
            ]
        ),
        height=300,
        show_index=False,
        sizing_mode="stretch_width",
        selectable="checkbox",
        pagination="local",
        page_size=15,
    )

    # Formulário de edição/criação
    contexto_id = pn.widgets.IntInput(name="ID", value=0, disabled=True)
    nome = pn.widgets.TextInput(name="Nome", placeholder="Nome do contexto")
    descricao = pn.widgets.TextAreaInput(
        name="Descrição", placeholder="Descrição do contexto", height=100
    )
    ativo = pn.widgets.Checkbox(name="Ativo", value=True)

    btn_novo = pn.widgets.Button(name="Novo", button_type="light")
    btn_salvar = pn.widgets.Button(name="Salvar", button_type="success")
    btn_excluir = pn.widgets.Button(name="Excluir", button_type="danger", disabled=True)

    def _load_grid(*events):
        print("[DEBUG Contextos _load_grid] Iniciando carregamento do grid")
        try:
            from conf.funcoesbd import contextos_listar

            dados = contextos_listar(engine, incluir_inativos=True)
            print(f"[DEBUG Contextos _load_grid] Dados recebidos: {dados}")
            grid.value = pd.DataFrame(dados)
            print(
                f"[DEBUG Contextos _load_grid] {len(dados)} contextos carregados no grid"
            )
        except Exception as e:
            _notify("error", f"Erro ao carregar contextos: {str(e)}")
            print(f"[DEBUG Contextos _load_grid] ERRO ao carregar: {e}")
            import traceback

            traceback.print_exc()

    def _limpar_formulario(*events):
        contexto_id.value = 0
        nome.value = ""
        descricao.value = ""
        ativo.value = True
        btn_excluir.disabled = True

    def _preencher_formulario(selected_rows):
        if not selected_rows:
            _limpar_formulario()
            return

        row = grid.value.iloc[selected_rows[0]]
        contexto_id.value = row["id"]
        nome.value = row["nome"]
        descricao.value = row["descricao"] or ""
        ativo.value = bool(row["ativo"])
        btn_excluir.disabled = False

    def _salvar(*events):
        print("=" * 80)
        print("[DEBUG Contextos _salvar] Botão salvar clicado")
        print(f"[DEBUG Contextos _salvar] ID atual: {contexto_id.value}")
        print(f"[DEBUG Contextos _salvar] Nome: '{nome.value}'")
        print(f"[DEBUG Contextos _salvar] Descrição: '{descricao.value}'")
        print(f"[DEBUG Contextos _salvar] Ativo: {ativo.value}")

        try:
            from conf.funcoesbd import contexto_inserir, contexto_atualizar

            dados = {
                "nome": (nome.value or "").strip(),
                "descricao": (descricao.value or "").strip(),
                "ativo": int(ativo.value),
            }

            print(f"[DEBUG Contextos _salvar] Dados preparados: {dados}")

            if not dados["nome"]:
                print("[DEBUG Contextos _salvar] Nome vazio, abortando")
                _notify("error", "Nome do contexto é obrigatório")
                return

            if contexto_id.value > 0:
                print(f"[DEBUG Contextos _salvar] Modo UPDATE - ID {contexto_id.value}")
                resultado = contexto_atualizar(engine, contexto_id.value, **dados)
                print(f"[DEBUG Contextos _salvar] Resultado UPDATE: {resultado}")
                _notify("success", f"Contexto '{dados['nome']}' atualizado com sucesso")
            else:
                print(f"[DEBUG Contextos _salvar] Modo INSERT")
                resultado = contexto_inserir(engine, criado_por=None, **dados)
                print(f"[DEBUG Contextos _salvar] Resultado INSERT: {resultado}")
                _notify("success", f"Contexto '{dados['nome']}' criado com sucesso")

            print("[DEBUG Contextos _salvar] Recarregando grid...")
            _load_grid()
            print("[DEBUG Contextos _salvar] Limpando formulário...")
            _limpar_formulario()
            print("[DEBUG Contextos _salvar] Salvamento concluído com sucesso")
            print("=" * 80)

        except Exception as e:
            _notify("error", f"Erro ao salvar contexto: {str(e)}")
            print(f"[DEBUG Contextos _salvar] EXCEÇÃO: {e}")
            import traceback

            traceback.print_exc()
            print("=" * 80)

    def _excluir(*events):
        print("=" * 80)
        print("[DEBUG Contextos _excluir] Botão excluir clicado")
        print(f"[DEBUG Contextos _excluir] ID do contexto: {contexto_id.value}")
        print(f"[DEBUG Contextos _excluir] Nome do contexto: '{nome.value}'")

        if not contexto_id.value:
            print("[DEBUG Contextos _excluir] ID vazio, abortando")
            _notify("warning", "Selecione um contexto para excluir")
            print("=" * 80)
            return

        try:
            from conf.funcoesbd import contexto_deletar, contexto_pode_deletar

            nome_ctx = nome.value
            ctx_id = contexto_id.value
            print(
                f"[DEBUG Contextos _excluir] Tentando excluir ID {ctx_id} - '{nome_ctx}'"
            )

            print(f"[DEBUG Contextos _excluir] Verificando se pode deletar...")
            pode_deletar = contexto_pode_deletar(engine, ctx_id)
            print(
                f"[DEBUG Contextos _excluir] Pode deletar? {pode_deletar} (tipo: {type(pode_deletar)})"
            )

            if not pode_deletar:
                print(f"[DEBUG Contextos _excluir] Bloqueado - existem dependências")
                _notify(
                    "error",
                    f"Não é possível excluir '{nome_ctx}' pois existem de/para associados a ele",
                )
                print("=" * 80)
                return

            print(f"[DEBUG Contextos _excluir] Executando deleção...")
            resultado = contexto_deletar(engine, ctx_id)
            print(
                f"[DEBUG Contextos _excluir] Resultado da deleção: {resultado} (tipo: {type(resultado)})"
            )

            if resultado:
                print(f"[DEBUG Contextos _excluir] Deleção bem-sucedida")
                _notify("success", f"Contexto '{nome_ctx}' excluído com sucesso")
                print("[DEBUG Contextos _excluir] Recarregando grid...")
                _load_grid()
                print("[DEBUG Contextos _excluir] Limpando formulário...")
                _limpar_formulario()
                print("[DEBUG Contextos _excluir] Exclusão concluída com sucesso")
            else:
                print(f"[DEBUG Contextos _excluir] Deleção retornou False ou None")
                _notify("error", f"Não foi possível excluir o contexto '{nome_ctx}'")

            print("=" * 80)

        except Exception as e:
            _notify("error", f"Erro ao excluir contexto: {str(e)}")
            print(f"[DEBUG Contextos _excluir] EXCEÇÃO: {e}")
            import traceback

            traceback.print_exc()
            print("=" * 80)

    # Event bindings
    grid.param.watch(lambda e: _preencher_formulario(e.new), "selection")
    btn_novo.on_click(_limpar_formulario)
    btn_salvar.on_click(_salvar)
    btn_excluir.on_click(_excluir)

    # Initial load
    _load_grid()

    return pn.Column(
        pn.pane.Markdown("### Gestão de Contextos"),
        pn.pane.Markdown(
            """Os contextos são utilizados para agrupar regras de de/para de colunas.
            Por exemplo: você pode ter um contexto 'Cielo' com um conjunto de regras e outro 'Stone' com regras diferentes."""
        ),
        grid,
        pn.layout.Divider(),
        pn.Row(
            pn.Column(
                "#### Formulário de Contexto",
                contexto_id,
                nome,
                descricao,
                ativo,
                pn.Row(btn_novo, btn_salvar, btn_excluir),
                width=400,
            ),
            sizing_mode="stretch_width",
        ),
        sizing_mode="stretch_width",
    )


# =========================
# VIEW PRINCIPAL DE GESTÃO
# =========================
def make_gestao_view(
    engine: Engine, usuario_logado: Optional[str]
) -> pn.viewable.Viewable:
    return pn.Tabs(
        ("Clientes", _make_tab_clientes(engine)),
        ("Contextos", _make_tab_contextos(engine)),
        ("Bandeiras", _make_tab_bandeiras_cadastro(engine)),
        ("Termos Filtráveis", _make_tab_termos_filtraveis(engine)),
        ("Bandeiras por EC", _make_tab_bandeiras(engine)),
        ("Taxas por EC", _make_tab_taxas(engine)),
        tabs_location="above",
        sizing_mode="stretch_both",
    )
