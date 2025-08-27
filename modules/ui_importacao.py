# modules/ui_importacao.py
import os
import tempfile
from typing import Optional, Dict, List

import pandas as pd
import panel as pn
from sqlalchemy.engine import Engine

# --------- BD helpers ----------
from conf.funcoesbd import (
    # De-Para
    depara_listar, depara_inserir, depara_atualizar, depara_deletar, depara_buscar_por_chave,
    # Listas dinâmicas
    listar_contextos, listar_colunas_mapeaveis,
    # Clientes / EC
    clientes_listar, ecs_por_cliente,
    # Controle de colunas
    colunas_controle_listar, colunas_controle_inserir, colunas_controle_atualizar,
    colunas_controle_deletar, colunas_controle_sincronizar,
)

# --------- Proc helpers ----------
from proc.proc_importacao import (
    preparar_dataframe_de_arquivo,
    normalizar_dataframe_vendas,
    classificar_e_gravar_vendas,
)

# fallback local caso detectar_cabecalho não exista no proc
try:
    from proc.proc_importacao import detectar_cabecalho
except Exception:
    def detectar_cabecalho(df: pd.DataFrame, min_preenchidos: int = 10) -> int:
        for i in range(len(df)):
            row = df.iloc[i]
            filled = sum(
                (pd.notna(v)) and (str(v).strip() != "")
                for v in row.tolist()
            )
            if filled >= min_preenchidos:
                return i
        return 0

# NÃO chame pn.extension aqui; está no main (com 'tabulator' e notifications=True)
TIPOS = ["V", "L"]


# =========================
# Utils locais
# =========================
def _notify(kind: str, msg: str):
    n = getattr(pn.state, "notifications", None)
    if not n:
        return
    fn = getattr(n, kind, None)
    if fn:
        try:
            fn(msg)
        except Exception:
            pass

def _ensure_option(select_widget: pn.widgets.Select, value: str):
    """Se 'value' ainda não está nas options do Select, adiciona."""
    v = (value or "").strip()
    if not v:
        return
    opts = list(select_widget.options)
    if v not in opts:
        opts.append(v)
        select_widget.options = opts

def _empty_depara_df() -> pd.DataFrame:
    return pd.DataFrame(columns=[
        "id", "origem_nome", "destino_nome", "contexto", "tipo_origem",
        "ativo", "criado_por", "criado_em", "atualizado_em"
    ])

def _empty_controle_df() -> pd.DataFrame:
    return pd.DataFrame(columns=[
        "id", "campo", "preenchimento", "mapeavel", "ativo", "created_at", "updated_at"
    ])


# =========================
# ABA: De-Para
# =========================
def _make_tab_depara(engine: Engine, usuario_logado: Optional[str]) -> pn.viewable.Viewable:
    grid = pn.widgets.Tabulator(
        _empty_depara_df(),
        height=420,
        sizing_mode="stretch_width",
        pagination="local",
        page_size=25,
        show_index=False,
        header_filters=True,
        selectable="checkbox",
    )

    # Carrega listas dinâmicas (Contextos e Destinos) do banco
    try:
        CONTEXTOS_VALIDOS = listar_contextos(engine)  # ['CIELO','REDE',...]
        if not CONTEXTOS_VALIDOS:
            raise ValueError("sem contextos")
    except Exception:
        CONTEXTOS_VALIDOS = ["CIELO", "REDE"]  # fallback

    try:
        DESTINOS_VALIDOS = listar_colunas_mapeaveis(engine)  # só mapeáveis/ativas
        if not DESTINOS_VALIDOS:
            raise ValueError("sem colunas mapeáveis")
    except Exception:
        DESTINOS_VALIDOS = ["Data_da_venda", "Bandeira", "Forma_de_pagamento"]

    # Formulário
    origem   = pn.widgets.Select(name="Origem (coluna no arquivo)", options=[], value=None)
    destino  = pn.widgets.Select(name="Destino (coluna padronizada)", options=DESTINOS_VALIDOS,
                                 value=(DESTINOS_VALIDOS[0] if DESTINOS_VALIDOS else None))
    contexto = pn.widgets.Select(name="Contexto", options=CONTEXTOS_VALIDOS,
                                 value=(CONTEXTOS_VALIDOS[0] if CONTEXTOS_VALIDOS else None))
    tipo     = pn.widgets.Select(name="Tipo", options=TIPOS, value="V")
    ativo    = pn.widgets.Checkbox(name="Ativo", value=True)

    # Amostra para ler cabeçalho
    amostra_file = pn.widgets.FileInput(name="Planilha (amostra p/ ler cabeçalho)", accept=".xlsx,.xls,.csv", multiple=False)
    btn_ler_cab  = pn.widgets.Button(name="Ler Cabeçalho", button_type="light")

    # Botões
    btn_novo      = pn.widgets.Button(name="Novo", button_type="light")
    btn_inserir   = pn.widgets.Button(name="Inserir", button_type="primary")
    btn_atualizar = pn.widgets.Button(name="Atualizar", button_type="success")
    btn_excluir   = pn.widgets.Button(name="Excluir", button_type="danger")
    btn_refresh   = pn.widgets.Button(name="Recarregar", button_type="light")
    msg           = pn.pane.Markdown("", sizing_mode="stretch_width")

    # ---- loaders ----
    def _load_grid(_=None):
        try:
            rows_v = depara_listar(engine, contexto="", tipo_origem="V")
            rows_l = depara_listar(engine, contexto="", tipo_origem="L")
            rows = (rows_v or []) + (rows_l or [])
            grid.value = pd.DataFrame(rows) if rows else _empty_depara_df()
            grid.selection = []
            msg.object = ""
        except Exception as e:
            grid.value = _empty_depara_df()
            grid.selection = []
            msg.object = "Tabela `depara_colunas` não encontrada ou erro ao carregar."
            _notify("error", f"De-Para indisponível: {e}")

    def _reload_selects_from_db(_=None):
        nonlocal CONTEXTOS_VALIDOS, DESTINOS_VALIDOS
        try:
            CONTEXTOS_VALIDOS = listar_contextos(engine) or CONTEXTOS_VALIDOS
            contexto.options = CONTEXTOS_VALIDOS
            if contexto.value not in contexto.options and contexto.options:
                contexto.value = contexto.options[0]
        except Exception:
            pass

        try:
            DESTINOS_VALIDOS = listar_colunas_mapeaveis(engine) or DESTINOS_VALIDOS
            destino.options = DESTINOS_VALIDOS
            if destino.value not in destino.options and destino.options:
                destino.value = destino.options[0]
        except Exception:
            pass

    # ---- ler cabeçalho da amostra para popular ORIGEM ----
    def on_ler_cabecalho(_=None):
        if not amostra_file.value:
            _notify("warning", "Selecione uma planilha de amostra.")
            return
        name = amostra_file.filename or "amostra.xlsx"
        suffix = ".xlsx" if name.lower().endswith((".xlsx", ".xls")) else ".csv"
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(amostra_file.value)
            tmp.flush()
            path = tmp.name
        try:
            if suffix in (".xlsx", ".xls"):
                df_raw = pd.read_excel(path, header=None)
            else:
                df_raw = pd.read_csv(path, header=None, sep=None, engine="python")
            idx_header = detectar_cabecalho(df_raw, min_preenchidos=10)
            header = df_raw.iloc[idx_header].tolist()
            cols = [str(x).strip() for x in header if str(x).strip()]
            if cols:
                origem.options = cols
                origem.value = cols[0]
                _notify("success", f"Cabeçalho lido (linha {idx_header}). {len(cols)} colunas carregadas.")
            else:
                _notify("warning", "Não foram encontradas colunas a partir da amostra.")
        except Exception as e:
            _notify("error", f"Falha ao ler cabeçalho da planilha: {e}")
        finally:
            try:
                os.unlink(path)
            except Exception:
                pass

    # ---- seleção única no grid ----
    def _on_selection(event):
        sel = list(event.new or [])
        if len(sel) > 1:
            grid.selection = [sel[-1]]
            return
        if not sel:
            return
        idx = sel[0]
        df = grid.value
        if not isinstance(df, pd.DataFrame) or idx >= len(df):
            return
        row = df.iloc[idx].to_dict()

        _ensure_option(origem, str(row.get("origem_nome", "") or ""))
        origem.value  = str(row.get("origem_nome", "") or "")

        _ensure_option(destino, str(row.get("destino_nome", "") or ""))
        destino.value = str(row.get("destino_nome", "") or (destino.options[0] if destino.options else None))

        _ensure_option(contexto, str(row.get("contexto", "") or ""))
        contexto.value= str(row.get("contexto", "") or (contexto.options[0] if contexto.options else None))

        tipo.value    = (str(row.get("tipo_origem", "V") or "V")).upper()
        ativo.value   = bool(row.get("ativo", 1))
        msg.object    = f"Editando ID {row.get('id','')}."

    # ---- ações ----
    def on_new(_=None):
        origem.value  = None
        if destino.options:
            destino.value = destino.options[0]
        if contexto.options:
            contexto.value = contexto.options[0]
        tipo.value    = "V"
        ativo.value   = True
        grid.selection = []
        msg.object     = "Incluindo novo de-para."

    def on_inserir(_=None):
        src = (origem.value or "").strip()
        dst = (destino.value or "").strip()
        ctx = (contexto.value or "").strip()
        tp  = (tipo.value or "V").strip().upper()
        if not src or not dst:
            _notify("warning", "Selecione a coluna de origem e o destino.")
            return
        if not ctx:
            _notify("warning", "Selecione o Contexto.")
            return
        if tp not in ("V", "L"):
            _notify("warning", "Tipo inválido (use V ou L).")
            return
        try:
            depara_inserir(
                engine,
                origem_nome=src,
                destino_nome=dst,
                contexto=ctx,
                tipo_origem=tp,
                ativo=1 if ativo.value else 0,
                criado_por=usuario_logado,
            )
            _notify("success", "De-para inserido.")
            _load_grid()
        except Exception as e:
            _notify("error", f"Falha ao inserir: {e}")

    def on_atualizar(_=None):
        sel = grid.selection or []
        if not sel:
            _notify("warning", "Selecione um registro para atualizar.")
            return
        src = (origem.value or "").strip()
        dst = (destino.value or "").strip()
        ctx = (contexto.value or "").strip()
        tp  = (tipo.value or "V").strip().upper()
        if not src or not dst:
            _notify("warning", "Selecione a coluna de origem e o destino.")
            return
        if not ctx:
            _notify("warning", "Selecione o Contexto.")
            return
        if tp not in ("V", "L"):
            _notify("warning", "Tipo inválido (use V ou L).")
            return
        try:
            df = grid.value
            current_id = int(df.iloc[sel[0]]["id"])

            # Evita colisão de UNIQUE com outro id
            outro = depara_buscar_por_chave(engine, origem_nome=src, contexto=ctx, tipo_origem=tp)
            if outro and int(outro["id"]) != current_id:
                _notify("error", f"Já existe um de-para com essa chave (ID {outro['id']}). Altere a chave ou use esse registro.")
                return

            depara_atualizar(
                engine, current_id,
                origem_nome=src,
                destino_nome=dst,
                contexto=ctx,
                tipo_origem=tp,
                ativo=1 if ativo.value else 0,
            )
            _notify("success", "De-para atualizado.")
            _load_grid()
        except Exception as e:
            _notify("error", f"Falha ao atualizar: {e}")

    def on_delete(_=None):
        sel = grid.selection
        if not sel:
            _notify("warning", "Selecione uma linha para excluir.")
            return
        try:
            df = grid.value
            depara_id = int(df.iloc[sel[0]]["id"])
            depara_deletar(engine, depara_id)
            _notify("success", "Registro excluído.")
            _load_grid()
        except Exception as e:
            _notify("error", f"Falha ao excluir: {e}")

    # ligações
    grid.param.watch(_on_selection, "selection")
    btn_ler_cab.on_click(on_ler_cabecalho)
    btn_novo.on_click(on_new)
    btn_inserir.on_click(on_inserir)
    btn_atualizar.on_click(on_atualizar)
    btn_excluir.on_click(on_delete)
    btn_refresh.on_click(lambda _: (_reload_selects_from_db(), _load_grid()))

    # carga inicial
    _reload_selects_from_db()
    _load_grid()

    return pn.Column(
        pn.pane.Markdown("### De-Para de Colunas"),
        grid,
        pn.layout.Divider(),
        pn.pane.Markdown("#### Formulário (mapeamento de colunas)"),
        pn.Row(
            pn.Column(
                pn.pane.Markdown("**1) Origem (arquivo):**"),
                amostra_file,
                pn.Row(btn_ler_cab),
                origem,
                sizing_mode="stretch_width",
            ),
            pn.Spacer(width=20),
            pn.Column(
                pn.pane.Markdown("**2) Destino (layout interno):**"),
                destino,
                sizing_mode="stretch_width",
            ),
            pn.Spacer(width=20),
            pn.Column(
                pn.pane.Markdown("**3) Contexto / Tipo:**"),
                contexto,
                tipo,
                ativo,
                sizing_mode="stretch_width",
            ),
            sizing_mode="stretch_width",
        ),
        pn.Row(btn_novo, btn_inserir, btn_atualizar, btn_excluir, btn_refresh),
        msg,
        sizing_mode="stretch_width",
    )


# =========================
# ABA: Importar (cliente/EC + gravar)
# =========================
def _make_tab_importar(engine: Engine, usuario_logado: Optional[str]) -> pn.viewable.Viewable:
    # Contextos (de tabela contextos)
    try:
        contextos = listar_contextos(engine)
    except Exception:
        contextos = ["CIELO", "REDE"]

    # Clientes -> options com rótulo "id - nome"
    try:
        _clientes = clientes_listar(engine)
        clientes_opts = {f"{c['cliente_id']} - {c.get('nome_fantasia') or c.get('razao_social') or 'Cliente'}": c["cliente_id"] for c in _clientes}
    except Exception:
        clientes_opts = {}

    cliente_select = pn.widgets.Select(name="Cliente", options=clientes_opts, value=(next(iter(clientes_opts.values())) if clientes_opts else None))
    ec_select = pn.widgets.Select(name="EC", options=[], value=None)

    def _load_ecs(_=None):
        ec_opts: List[int] = []
        cid = cliente_select.value
        if cid is not None:
            try:
                ec_opts = ecs_por_cliente(engine, int(cid))  # List[int]
            except Exception:
                ec_opts = []
        ec_select.options = ec_opts
        ec_select.value = ec_opts[0] if ec_opts else None

    cliente_select.param.watch(_load_ecs, "value")
    _load_ecs()

    contexto_select = pn.widgets.Select(name="Contexto (Operadora)", options=[""] + contextos, value="")
    tipo_select     = pn.widgets.Select(name="Tipo", options=TIPOS, value="V")
    file_input      = pn.widgets.FileInput(accept=".xlsx,.xls,.csv", multiple=False)
    sheet_input     = pn.widgets.TextInput(name="Planilha (opcional)", placeholder="Ex.: Plan1")

    btn_processar   = pn.widgets.Button(name="Processar", button_type="primary")
    btn_normalizar  = pn.widgets.Button(name="Normalizar preview", button_type="light")
    btn_gravar      = pn.widgets.Button(name="Gravar", button_type="success")

    info    = pn.pane.Markdown("", sizing_mode="stretch_width")
    resumo  = pn.pane.Markdown("", sizing_mode="stretch_width")
    preview = pn.widgets.Tabulator(pd.DataFrame(), height=320, sizing_mode="stretch_width", show_index=False)

    state: Dict[str, Optional[pd.DataFrame]] = {"df": None, "arquivo": ""}

    def on_process(_=None):
        if not file_input.value:
            _notify("warning", "Selecione um arquivo.")
            return
        suffix = ".xlsx" if file_input.filename.lower().endswith((".xlsx", ".xls")) else ".csv"
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(file_input.value)
            tmp.flush()
            path = tmp.name
        try:
            df, transf, idx = preparar_dataframe_de_arquivo(
                path=path,
                engine=engine,
                contexto=(contexto_select.value or ""),
                tipo_origem=tipo_select.value,
                sheet_name=(sheet_input.value or None),
            )
            state["df"] = df.copy()
            state["arquivo"] = file_input.filename or os.path.basename(path)
            header_info = f"- Linha de cabeçalho detectada: **{idx}** (0-based)"
            if transf:
                tr = "\n".join([f"- {k} → {v}" for k, v in transf.items()])
                info.object = f"{header_info}\n- Transformações aplicadas:\n\n{tr}"
            else:
                info.object = f"{header_info}\n- Sem transformações (nenhum de-para correspondente)."
            preview.value = df.head(200)
            resumo.object = ""
            _notify("success", "Arquivo processado.")
        except Exception as e:
            _notify("error", f"Falha ao processar: {e}")
        finally:
            try:
                os.unlink(path)
            except Exception:
                pass

    def on_normalizar(_=None):
        if state["df"] is None:
            _notify("warning", "Processe um arquivo primeiro.")
            return
        try:
            df_norm = normalizar_dataframe_vendas(state["df"], usuario=usuario_logado or "desconhecido")
            state["df"] = df_norm
            preview.value = df_norm.head(200)
            _notify("success", "Preview normalizado.")
        except Exception as e:
            _notify("error", f"Falha ao normalizar: {e}")

    def on_gravar(_=None):
        if state["df"] is None:
            _notify("warning", "Processe um arquivo primeiro.")
            return
        if cliente_select.value is None or ec_select.value is None:
            _notify("warning", "Selecione Cliente e EC.")
            return
        try:
            df_to_save = normalizar_dataframe_vendas(state["df"].copy(), usuario=usuario_logado or "desconhecido")
            result = classificar_e_gravar_vendas(
                engine,
                df_to_save,
                cliente_id=int(cliente_select.value),
                ec_id=int(ec_select.value),
                contexto=(contexto_select.value or ""),
                usuario=usuario_logado or "desconhecido",
                arquivo_origem=(state["arquivo"] or ""),
                remover_duplicadas=True,
            )
            resumo.object = (
                f"**Processamento:** `{result['processamentoid']}`  \n"
                f"- Gravadas em **vendas_processadas**: **{result['processadas']}**  \n"
                f"- Gravadas em **vendas_filtradas**: **{result['filtradas']}**  \n"
                f"- **Total**: **{result['total']}**"
            )
            _notify("success", "Gravação concluída.")
        except Exception as e:
            _notify("error", f"Falha ao gravar: {e}")

    btn_processar.on_click(on_process)
    btn_normalizar.on_click(on_normalizar)
    btn_gravar.on_click(on_gravar)

    return pn.Column(
        pn.pane.Markdown("### Importar Arquivo (detectar cabeçalho, aplicar de-para e gravar)"),
        pn.Row(cliente_select, ec_select, contexto_select, tipo_select),
        pn.Row(file_input, sheet_input, btn_processar, btn_normalizar, btn_gravar),
        pn.layout.Divider(),
        info,
        preview,
        pn.layout.Divider(),
        pn.pane.Markdown("### Resultado da Gravação"),
        resumo,
        sizing_mode="stretch_width",
    )


# =========================
# ABA: Controle de Colunas (vendas_colunas_controle)
# =========================
def _make_tab_controle_colunas(engine: Engine) -> pn.viewable.Viewable:
    grid = pn.widgets.Tabulator(
        _empty_controle_df(),
        height=420,
        sizing_mode="stretch_width",
        pagination="local",
        page_size=25,
        show_index=False,
        header_filters=True,
        selectable="checkbox",
    )

    campo         = pn.widgets.TextInput(name="Campo (nome da coluna)")
    preenchimento = pn.widgets.Select(name="Preenchimento", options=["importado", "calculado", "sistema"], value="importado")
    mapeavel      = pn.widgets.Checkbox(name="Mapeável", value=True)
    ativo         = pn.widgets.Checkbox(name="Ativo", value=True)

    btn_novo     = pn.widgets.Button(name="Novo", button_type="light")
    btn_inserir  = pn.widgets.Button(name="Inserir", button_type="primary")
    btn_atualizar= pn.widgets.Button(name="Atualizar", button_type="success")
    btn_excluir  = pn.widgets.Button(name="Excluir", button_type="danger")
    btn_sync     = pn.widgets.Button(name="Sincronizar com tabela real", button_type="warning")
    btn_refresh  = pn.widgets.Button(name="Recarregar", button_type="light")
    msg          = pn.pane.Markdown("", sizing_mode="stretch_width")

    def _load(_=None):
        try:
            rows = colunas_controle_listar(engine)
            grid.value = pd.DataFrame(rows) if rows else _empty_controle_df()
            grid.selection = []
            msg.object = ""
        except Exception as e:
            grid.value = _empty_controle_df()
            grid.selection = []
            msg.object = "Erro ao carregar controle de colunas."
            _notify("error", f"Controle indisponível: {e}")

    def _on_selection(event):
        sel = list(event.new or [])
        if len(sel) > 1:
            grid.selection = [sel[-1]]
            return
        if not sel:
            return
        idx = sel[0]
        df = grid.value
        if not isinstance(df, pd.DataFrame) or idx >= len(df):
            return
        row = df.iloc[idx].to_dict()

        campo.value         = str(row.get("campo", "") or "")
        preenchimento.value = str(row.get("preenchimento", "importado") or "importado")
        mapeavel.value      = bool(row.get("mapeavel", 1))
        ativo.value         = bool(row.get("ativo", 1))
        msg.object          = f"Editando ID {row.get('id','')}."

    def on_new(_=None):
        campo.value         = ""
        preenchimento.value = "importado"
        mapeavel.value      = True
        ativo.value         = True
        grid.selection      = []
        msg.object          = "Incluindo novo campo."

    def on_inserir(_=None):
        c = (campo.value or "").strip()
        if not c:
            _notify("warning", "Informe o nome do campo.")
            return
        try:
            colunas_controle_inserir(
                engine,
                campo=c,
                preenchimento=preenchimento.value,
                mapeavel=1 if mapeavel.value else 0,
                ativo=1 if ativo.value else 0,
            )
            _notify("success", "Campo inserido.")
            _load()
        except Exception as e:
            _notify("error", f"Falha ao inserir: {e}")

    def on_atualizar(_=None):
        sel = grid.selection or []
        if not sel:
            _notify("warning", "Selecione um registro para atualizar.")
            return
        try:
            df = grid.value
            col_id = int(df.iloc[sel[0]]["id"])
            colunas_controle_atualizar(
                engine, col_id,
                campo=(campo.value or "").strip(),
                preenchimento=preenchimento.value,
                mapeavel=1 if mapeavel.value else 0,
                ativo=1 if ativo.value else 0,
            )
            _notify("success", "Campo atualizado.")
            _load()
        except Exception as e:
            _notify("error", f"Falha ao atualizar: {e}")

    def on_delete(_=None):
        sel = grid.selection
        if not sel:
            _notify("warning", "Selecione um registro para excluir.")
            return
        try:
            df = grid.value
            col_id = int(df.iloc[sel[0]]["id"])
            colunas_controle_deletar(engine, col_id)
            _notify("success", "Registro excluído.")
            _load()
        except Exception as e:
            _notify("error", f"Falha ao excluir: {e}")

    def on_sync(_=None):
        try:
            result = colunas_controle_sincronizar(engine)
            _notify("success", f"Sincronizado. Inseridos: {result.get('inseridos', 0)}.")
            _load()
        except Exception as e:
            _notify("error", f"Falha ao sincronizar: {e}")

    grid.param.watch(_on_selection, "selection")
    btn_novo.on_click(on_new)
    btn_inserir.on_click(on_inserir)
    btn_atualizar.on_click(on_atualizar)
    btn_excluir.on_click(on_delete)
    btn_sync.on_click(on_sync)
    btn_refresh.on_click(_load)

    _load()

    return pn.Column(
        pn.pane.Markdown("### Controle de Colunas (vendas_colunas_controle)"),
        grid,
        pn.layout.Divider(),
        pn.pane.Markdown("#### Formulário"),
        pn.Row(campo, preenchimento, mapeavel, ativo),
        pn.Row(btn_novo, btn_inserir, btn_atualizar, btn_excluir, btn_sync, btn_refresh),
        msg,
        sizing_mode="stretch_width",
    )


# =========================
# View pública (Tabs)
# =========================
def make_importacao_view(engine: Engine, usuario_logado: Optional[str]) -> pn.viewable.Viewable:
    aba_importar = _make_tab_importar(engine, usuario_logado)
    aba_depara   = _make_tab_depara(engine, usuario_logado)
    aba_ctrl     = _make_tab_controle_colunas(engine)
    return pn.Tabs(
        ("Importar Arquivo", aba_importar),
        ("De-Para de Colunas", aba_depara),
        ("Controle de Colunas", aba_ctrl),
        tabs_location="above",
        sizing_mode="stretch_both",
    )
