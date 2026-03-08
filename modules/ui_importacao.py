# modules/ui_importacao.py
import os
import tempfile
from typing import Optional, Dict, List, Any

import pandas as pd
import panel as pn
from sqlalchemy.engine import Engine

from conf.funcoesbd import (
    depara_listar,
    depara_inserir,
    depara_atualizar,
    depara_deletar,
    listar_contextos,
    contextos_listar,
    clientes_listar,
    ecs_por_cliente,
    listar_colunas_vendas_processadas,
    listar_processamentoids,
    listar_processamentos_detalhado,
    deletar_processamento,
)
from modules.ui_theme import create_glass_card, premium_metric

from proc.proc_importacao import (
    preparar_dataframe_de_arquivo,
    normalizar_dataframe_vendas,
    # --- ALTERAÇÃO 1: Adicionar a importação da função de recebíveis ---
    normalizar_dataframe_recebiveis,
    classificar_e_gravar_vendas,
    preparar_para_tabulator,
    detectar_cabecalho,
    safe_read_file,
)

TIPOS = ["V", "L", "R"]


def _notify(kind: str, msg: str):
    if n := getattr(pn.state, "notifications", None):
        if hasattr(n, kind):
            getattr(n, kind)(msg)


def _ensure_option(select_widget: pn.widgets.Select, value: str):
    v = (value or "").strip()
    if not v:
        return
    opts = list(select_widget.options)
    if v not in opts:
        opts.append(v)
        select_widget.options = opts


def _empty_depara_df() -> pd.DataFrame:
    return pd.DataFrame(
        columns=[
            "id",
            "origem_nome",
            "destino_nome",
            "contexto",
            "tipo_origem",
            "ativo",
            "tipo_preenchimento",
            "valor_padrao",
        ]
    )


def _make_tab_depara(
    engine: Engine, usuario_logado: Optional[str]
) -> pn.viewable.Viewable:
    progress_leitura = pn.widgets.Progress(
        name="Leitura do Arquivo", value=0, max=100, visible=False, width=300
    )
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

    contexto_select = pn.widgets.Select(name="Contexto", options=[])
    tipo_select = pn.widgets.Select(name="Tipo (V/L/R)", options=TIPOS, value="V")
    destino_select = pn.widgets.Select(name="Destino (Coluna no sistema)", options=[])

    def atualizar_destino_select(event=None):
        tipo = tipo_select.value
        try:
            if tipo == "R":
                # Buscar colunas da tabela recebiveis_processados
                from sqlalchemy import inspect

                insp = inspect(engine)
                cols = [
                    col["name"] for col in insp.get_columns("recebiveis_processados")
                ]
                destino_select.options = cols
            else:
                # Buscar apenas colunas mapeáveis da tabela depara_controle
                import sqlalchemy

                with engine.connect() as conn:
                    result = conn.execute(
                        sqlalchemy.text(
                            "SELECT nome_coluna FROM depara_controle WHERE mapeavel = 'mapeavel' ORDER BY id"
                        )
                    )
                    destinos_mapeaveis = [row[0] for row in result]
                destino_select.options = destinos_mapeaveis
        except Exception as e:
            _notify("error", f"Erro ao carregar colunas destino: {e}")

    tipo_select.param.watch(atualizar_destino_select, "value")
    tipo_preenchimento_select = pn.widgets.Select(
        name="Tipo de Preenchimento",
        options=["importado", "padrão", "sistema", "ignorar"],
        value="importado",
    )

    # O widget de origem começa como um TextInput, mas será referenciado por uma lista para permitir troca dinâmica
    origem_input_widget = [
        pn.widgets.TextInput(
            name="Origem (Coluna no arquivo)",
            placeholder="Obrigatório para 'importado'",
        )
    ]

    valor_padrao_input = pn.widgets.TextInput(name="Valor Padrão (para tipo 'padrão')")
    ativo_check = pn.widgets.Checkbox(name="Ativo", value=True)

    amostra_file = pn.widgets.FileInput(
        name="Ler colunas de arquivo de amostra",
        accept=".xlsx,.xls,.csv",
        multiple=False,
    )
    btn_ler_cabecalho = pn.widgets.Button(name="Ler Cabeçalho", button_type="primary")

    btn_novo = pn.widgets.Button(name="Novo", button_type="light")
    btn_inserir = pn.widgets.Button(name="Inserir", button_type="primary")
    btn_atualizar = pn.widgets.Button(name="Atualizar", button_type="success")
    btn_excluir = pn.widgets.Button(name="Excluir", button_type="danger")
    btn_refresh = pn.widgets.Button(name="Recarregar", button_type="light")
    msg_pane = pn.pane.Markdown("")

    def _load_grid(*events):
        try:
            rows = depara_listar(engine)
            grid.value = pd.DataFrame(rows).fillna("") if rows else _empty_depara_df()
            grid.selection = []
        except Exception as e:
            _notify("error", f"Erro ao carregar De-Para: {e}")

    def _load_selects_from_db():
        try:
            current_ctx = contexto_select.value
            current_dst = destino_select.value

            # Obter contextos da tabela de contextos (não apenas os usados em depara_colunas)
            contextos = contextos_listar(engine)
            contexto_select.options = [c["nome"] for c in contextos]

            # Buscar apenas colunas mapeáveis da tabela depara_controle
            import sqlalchemy

            with engine.connect() as conn:
                result = conn.execute(
                    sqlalchemy.text(
                        "SELECT nome_coluna FROM depara_controle WHERE mapeavel = 'mapeavel' ORDER BY id"
                    )
                )
                destinos_mapeaveis = [row[0] for row in result]
            destino_select.options = destinos_mapeaveis
            if current_ctx in contexto_select.options:
                contexto_select.value = current_ctx
            if current_dst in destino_select.options:
                destino_select.value = current_dst
        except Exception as e:
            _notify("error", f"Erro ao carregar listas do BD: {e}")

    def on_selection(event):
        if not event.new:
            return
        row = grid.value.iloc[event.new[0]].to_dict()

        origem_input_widget[0].value = str(row.get("origem_nome", "") or "")
        _ensure_option(destino_select, row.get("destino_nome", ""))
        destino_select.value = row.get("destino_nome", "")
        _ensure_option(contexto_select, row.get("contexto", ""))
        contexto_select.value = row.get("contexto", "")
        tipo_select.value = row.get("tipo_origem", "V")
        ativo_check.value = bool(row.get("ativo", 1))
        tipo_preenchimento_select.value = row.get("tipo_preenchimento", "importado")
        valor_padrao_input.value = str(row.get("valor_padrao", "") or "")
        msg_pane.object = f"Editando ID {row.get('id', '')}..."

    grid.param.watch(on_selection, "selection")

    def on_novo(*events):
        grid.selection = []
        origem_input_widget[0].value = ""
        valor_padrao_input.value = ""
        ativo_check.value = True
        tipo_preenchimento_select.value = "importado"
        msg_pane.object = "Preencha os campos para um novo registro."

    btn_novo.on_click(on_novo)

    def on_action(action_type):
        try:
            tipo_preenchimento = tipo_preenchimento_select.value

            if not destino_select.value or not contexto_select.value:
                return _notify("warning", "Contexto e Destino são obrigatórios.")
            if tipo_preenchimento == "importado" and not origem_input_widget[0].value:
                return _notify("warning", "Para 'importado', a Origem é obrigatória.")
            if tipo_preenchimento == "padrão" and not valor_padrao_input.value:
                return _notify(
                    "warning", "Para 'padrão', o Valor Padrão é obrigatório."
                )

            params = {
                "origem_nome": origem_input_widget[0].value or None,
                "destino_nome": destino_select.value,
                "contexto": contexto_select.value,
                "tipo_origem": tipo_select.value,
                "ativo": int(ativo_check.value),
                "tipo_preenchimento": tipo_preenchimento,
                "valor_padrao": valor_padrao_input.value or None,
            }
            if action_type == "insert":
                params["criado_por"] = usuario_logado
                depara_inserir(engine, **params)
                _notify("success", "De-para inserido.")
            elif action_type in ["update", "delete"]:
                if not grid.selection:
                    return _notify("warning", "Selecione um item.")
                depara_id = int(grid.value.iloc[grid.selection[0]]["id"])
                if action_type == "update":
                    depara_atualizar(engine, depara_id, **params)
                    _notify("success", "De-para atualizado.")
                else:
                    depara_deletar(engine, depara_id)
                    _notify("success", "De-para excluído.")
            _load_grid()
        except Exception as e:
            _notify("error", f"Falha na operação: {e}")

    btn_inserir.on_click(lambda e: on_action("insert"))
    btn_atualizar.on_click(lambda e: on_action("update"))
    btn_excluir.on_click(lambda e: on_action("delete"))
    btn_refresh.on_click(lambda e: (_load_selects_from_db(), _load_grid()))

    def on_ler_cabecalho(*events):
        progress_leitura.visible = True
        progress_leitura.value = 10
        if not amostra_file.value:
            progress_leitura.visible = False
            return _notify("warning", "Selecione um arquivo de amostra.")

        import mimetypes
        import os

        filename = (
            amostra_file.filename
            if hasattr(amostra_file, "filename") and amostra_file.filename
            else None
        )
        ext = os.path.splitext(filename)[-1] if filename else ".tmp"
        if ext.lower() not in [".xlsx", ".xls", ".csv"]:
            ext = ".tmp"
        import base64

        file_bytes = amostra_file.value
        if isinstance(file_bytes, str):
            try:
                file_bytes = base64.b64decode(file_bytes)
            except Exception:
                pass
        with tempfile.NamedTemporaryFile(delete=False, suffix=ext, mode="wb") as tmp:
            tmp.write(file_bytes)
            path = tmp.name
        try:
            progress_leitura.value = 30

            # Importar as funções de multi-sheet
            from proc.proc_importacao import (
                is_multisheet_rede_file,
                safe_read_multisheet_file,
            )

            # Verificar se é arquivo multi-sheet (independente de contexto)
            if is_multisheet_rede_file(path):
                print("[DEBUG] Detectado arquivo multi-planilhas, processando...")
                multisheet_data = safe_read_multisheet_file(path, tipo_select.value)

                # Coletar todas as colunas de todas as planilhas
                all_headers = []
                for sheet_name, sheet_info in multisheet_data.items():
                    headers = sheet_info["headers"]
                    all_headers.extend(headers)
                    print(f"[DEBUG] {sheet_name}: {len(headers)} colunas")

                header_cols = all_headers
                print("[DEBUG] Total de colunas multi-sheet:", len(header_cols))

            else:
                print("[DEBUG] Arquivo single-sheet, usando safe_read_file...")
                df_raw, _, header_cols = safe_read_file(path)

            print("[DEBUG] DataFrame carregado com sucesso")
            print("[DEBUG] Colunas detectadas:", header_cols)
            progress_leitura.value = 70

            header_values = list(header_cols)
            cols = [""] + header_values  # Adiciona opção vazia no início

            print("[DEBUG] Colunas para o select box:", cols)
            if cols:
                novo_select = pn.widgets.Select(
                    name="Origem (Coluna no arquivo)", options=cols
                )
                form_layout_col2[1] = novo_select
                origem_input_widget[0] = novo_select
                _notify(
                    "success", f"Cabeçalho lido. {len(cols) - 1} colunas carregadas."
                )
                progress_leitura.value = 100
            else:
                _notify("warning", "Não foram encontradas colunas na amostra.")
                progress_leitura.value = 0
        except Exception as e:
            progress_leitura.value = 0
            msg = str(e)
            if (
                "binário ou corrompido" in msg.lower()
                or "cannot convert float infinity to integer" in msg.lower()
                or "excel" in msg.lower()
            ):
                _notify(
                    "error",
                    "Falha ao ler o arquivo: o arquivo pode estar corrompido. Abra e salve novamente no Excel antes de importar. Se necessário, utilize a função 'Salvar como' no Excel para gerar um novo arquivo .xlsx.\n\nErro técnico: "
                    + msg,
                )
            else:
                _notify("error", f"Falha ao ler o arquivo: {e}")
        finally:
            progress_leitura.visible = False
            if os.path.exists(path):
                os.unlink(path)

    btn_ler_cabecalho.on_click(on_ler_cabecalho)

    _load_selects_from_db()
    _load_grid()

    form_layout_col2 = pn.Column(
        tipo_preenchimento_select,
        origem_input_widget[0],
        valor_padrao_input,
        progress_leitura,
        sizing_mode="stretch_width",
    )

    form_layout = pn.Row(
        pn.Column(
            contexto_select, tipo_select, destino_select, sizing_mode="stretch_width"
        ),
        form_layout_col2,
        pn.Column(
            pn.layout.Spacer(height=25), ativo_check, sizing_mode="stretch_width"
        ),
    )

    return pn.Column(
        pn.pane.Markdown("# Mapeamento De-Para", css_classes=["premium-header"]),
        create_glass_card(
            pn.Column(
                pn.Row(btn_refresh),
                grid,
            ),
            title="📋 Regras de Mapeamento"
        ),
        pn.Spacer(height=20),
        create_glass_card(
            pn.Column(
                pn.Row(amostra_file, btn_ler_cabecalho, align="end"),
                form_layout,
                pn.Row(btn_novo, btn_inserir, btn_atualizar, btn_excluir),
                msg_pane,
            ),
            title="🛠️ Configurar Novo Campo"
        ),
        sizing_mode="stretch_width",
        margin=(10, 20)
    )


def _make_tab_importar(
    engine: Engine, usuario_logado: Optional[str]
) -> pn.viewable.Viewable:
    # Botão para atualizar o selectbox de ProcessamentoID anterior
    btn_atualizar_processamentoid = pn.widgets.Button(
        name="🔄 Atualizar Processamentos", button_type="primary", width=180
    )
    # Tabulator de debug para mostrar o DataFrame bruto lido do arquivo
    debug_tabulator = pn.widgets.Tabulator(
        pd.DataFrame(),
        height=220,
        sizing_mode="stretch_width",
        show_index=False,
        header_filters=True,
        name="Debug DataFrame Bruto (SafeReadFile)",
    )
    btn_reset = pn.widgets.Button(
        name="🧹 Limpar Importação", button_type="warning", width=180
    )

    def on_reset(_=None):
        # Limpa todos os campos e estado da importação
        file_input.value = None
        file_input.filename = None
        state["arquivos"] = []
        state["idx_preview"] = 0
        preview.value = pd.DataFrame()
        arquivos_tabulator.value = pd.DataFrame(
            columns=["#", "Arquivo", "Linhas", "Status"]
        )
        info.object = ""
        resumo.object = ""
        progress_importacao.value = 0
        progress_importacao.visible = False
        _notify("info", "Importação limpa. Pronto para novo upload.")

    btn_reset.on_click(on_reset)
    # CONTINUAR PROCESSAMENTOID
    continuar_checkbox = pn.widgets.Checkbox(
        name="✓ Continuar processamento anterior",
        value=False,
        width=250,
        margin=(5, 10),
    )
    try:
        ids = listar_processamentoids(engine)
        print(f"[DEBUG] ProcessamentoIDs encontrados: {ids}")
        processamentoid_select = pn.widgets.Select(
            name="ProcessamentoID anterior",
            options=ids or [],
            visible=True,
            width=250,
            margin=(5, 10),
        )
    except Exception as e:
        print(f"[DEBUG] Erro ao buscar IDs: {e}")
        processamentoid_select = pn.widgets.Select(
            name="ProcessamentoID anterior",
            options=[],
            visible=True,
            width=250,
            margin=(5, 10),
        )

    def atualizar_processamentoid_select(event=None):
        try:
            ids = listar_processamentoids(engine)
            print(f"[DEBUG] Atualizando ProcessamentoIDs: {ids}")
            processamentoid_select.options = ids or []
            _notify("success", "Lista de ProcessamentoID atualizada.")
        except Exception as e:
            print(f"[DEBUG] Erro ao atualizar ProcessamentoIDs: {e}")
            processamentoid_select.options = []
            _notify("error", f"Erro ao atualizar ProcessamentoID: {e}")

    btn_atualizar_processamentoid.on_click(atualizar_processamentoid_select)

    progress_importacao = pn.widgets.Progress(
        name="Processo de Importação", value=0, max=100, visible=False, width=300
    )

    try:
        contextos_list = contextos_listar(engine)
        contextos = [c["nome"] for c in contextos_list]
    except Exception:
        contextos = ["CIELO", "REDE"]

    try:
        _clientes = clientes_listar(engine)
        clientes_opts = {
            f"{c['cliente_id']} - {c.get('nome_fantasia') or 'Cliente'}": c[
                "cliente_id"
            ]
            for c in _clientes
        }
    except Exception:
        clientes_opts = {}

    cliente_select = pn.widgets.Select(name="Cliente", options=clientes_opts)
    ec_select = pn.widgets.Select(name="EC", options=[])

    def _load_ecs(*events):
        cid = cliente_select.value
        try:
            ec_opts = ecs_por_cliente(engine, int(cid)) if cid else []
            ec_select.options = ec_opts
        except Exception:
            ec_select.options = []

    cliente_select.param.watch(_load_ecs, "value", onlychanged=True)
    pn.state.onload(_load_ecs)

    contexto_select = pn.widgets.Select(name="Contexto (Layout)", options=contextos)
    tipo_select = pn.widgets.Select(
        name="Tipo de Arquivo",
        options={"Venda": "V", "Lançamento": "L", "Recebíveis": "R"},
        value="V",
    )
    file_input = pn.widgets.FileInput(accept=".xlsx,.xls,.csv", multiple=True)

    btn_processar = pn.widgets.Button(
        name="Processar e Normalizar", button_type="primary"
    )
    btn_gravar = pn.widgets.Button(name="Gravar no Banco", button_type="success")

    info = pn.pane.Markdown("", sizing_mode="stretch_width")
    resumo = pn.Column(sizing_mode="stretch_width")
    preview = pn.widgets.Tabulator(
        pd.DataFrame(),
        height=320,
        sizing_mode="stretch_width",
        show_index=False,
        header_filters=True,
    )
    arquivos_processados = []  # Lista de dicts: {arquivo, df, transf, idx}
    state: Dict[str, Any] = {"arquivos": arquivos_processados, "idx_preview": 0}

    def on_process(_=None):
        btn_processar.name = "Processando..."
        btn_processar.button_type = "warning"
        btn_processar.disabled = True
        progress_importacao.visible = True
        progress_importacao.value = 5
        info.object = (
            "[DEBUG] Botão 'Processar e Normalizar' clicado. Iniciando processamento."
        )
        _notify("info", "[DEBUG] Botão 'Processar e Normalizar' foi clicado.")
        if not file_input.value:
            progress_importacao.visible = False
            btn_processar.name = "Processar e Normalizar"
            btn_processar.button_type = "primary"
            btn_processar.disabled = False
            return _notify("warning", "Selecione um ou mais arquivos.")
        if not contexto_select.value:
            progress_importacao.visible = False
            btn_processar.name = "Processar e Normalizar"
            btn_processar.button_type = "primary"
            btn_processar.disabled = False
            return _notify("warning", "Selecione um Contexto (Layout).")

        files = (
            file_input.value
            if isinstance(file_input.value, list)
            else [file_input.value]
        )
        filenames = (
            file_input.filename
            if isinstance(file_input.filename, list)
            else [file_input.filename]
        )
        resultados = []
        debug_tabulator.value = pd.DataFrame()  # Limpa debug
        total_files = len(files)

        # Gerar processamentoid único se não for continuar
        processamentoid_novo = None
        if continuar_checkbox.value and processamentoid_select.value:
            state["processamentoid"] = processamentoid_select.value
        else:
            from conf.funcoesbd import processamento_gerar_novo_id, processamento_salvar
            import datetime

            now = datetime.datetime.now()
            ec_id = ec_select.value  # ec_id agora é VARCHAR, não INT
            cliente_id = int(cliente_select.value)
            processamentoid_novo, data_proc = processamento_gerar_novo_id(
                engine, ec_id, now
            )
            processamento_salvar(
                engine,
                ec_id,
                cliente_id,
                processamentoid_novo,
                f"Processamento {now:%d/%m/%Y %H:%M}",
                data_proc,
            )
            state["processamentoid"] = processamentoid_novo

        for idx_file, (file_bytes, fname) in enumerate(zip(files, filenames)):
            if file_bytes is None:
                _notify(
                    "warning",
                    f"Arquivo '{fname}' está vazio ou não foi carregado corretamente. Ignorando.",
                )
                continue
            ext = os.path.splitext(fname)[-1] if fname else ".tmp"
            if ext.lower() not in [".xlsx", ".xls", ".csv"]:
                ext = ".tmp"
            import base64

            if isinstance(file_bytes, str):
                try:
                    file_bytes = base64.b64decode(file_bytes)
                except Exception:
                    pass
            with tempfile.NamedTemporaryFile(
                delete=False, suffix=ext, mode="wb"
            ) as tmp:
                tmp.write(file_bytes)
                path = tmp.name
            try:
                # --- DEBUG: Mostra DataFrame bruto lido do arquivo ---
                from proc.proc_importacao import safe_read_file

                df_raw, header_idx, header_cols = safe_read_file(path)
                debug_tabulator.value = df_raw.head(200)
                # --- Fim debug ---

                def progress_cb(val):
                    # Progresso global: cada arquivo ocupa fatia igual
                    base = int(100 * idx_file / max(1, total_files))
                    span = int(100 / max(1, total_files))
                    progress_importacao.value = min(100, base + int(val * span / 100))

                def log_cb(msg):
                    info.object = f"**{fname}:** {msg}"

                from proc.proc_importacao import preparar_dataframe_de_arquivo

                df_mapeado, transf, idx = preparar_dataframe_de_arquivo(
                    path=path,
                    engine=engine,
                    contexto=contexto_select.value,
                    tipo_origem=tipo_select.value,
                    progress_callback=progress_cb,
                    log_callback=log_cb,
                )

                # --- ALTERAÇÃO 2: Chamar a função correta baseada no tipo de arquivo ---
                tipo_arquivo_selecionado = tipo_select.value

                if tipo_arquivo_selecionado == "R":
                    df_normalizado = normalizar_dataframe_recebiveis(
                        df_mapeado,
                        engine=engine,
                        ec_id=ec_select.value,  # ec_id agora é VARCHAR, não INT
                        contexto=contexto_select.value,
                        usuario=usuario_logado,
                    )
                else:  # 'V' ou 'L'
                    df_processadas, df_filtradas = normalizar_dataframe_vendas(
                        df_mapeado,
                        engine=engine,
                        ec_id=ec_select.value,  # ec_id agora é VARCHAR, não INT
                        contexto=contexto_select.value,
                        usuario=usuario_logado,
                        tipo_arquivo=tipo_arquivo_selecionado,
                    )

                    # Combinar processadas e filtradas em um único DataFrame
                    if len(df_filtradas) > 0:
                        df_normalizado = pd.concat(
                            [df_processadas, df_filtradas], ignore_index=True
                        )
                    else:
                        df_normalizado = df_processadas
                # --- FIM DA ALTERAÇÃO ---

                resultados.append(
                    {
                        "arquivo": fname,
                        "df": df_normalizado.copy(),
                        "transf": transf,
                        "idx": idx,
                        "processamentoid": state["processamentoid"],
                    }
                )
            except Exception as e:
                _notify("error", f"Falha ao processar {fname}: {e}")
                info.object = f"**Erro em {fname}:** {e}"
            finally:
                if os.path.exists(path):
                    try:
                        # Tentar fechar qualquer handle aberto
                        import gc

                        gc.collect()
                        # Pequena pausa para permitir que o sistema libere o arquivo
                        import time

                        time.sleep(0.1)
                        os.unlink(path)
                    except PermissionError as pe:
                        print(
                            f"[DEBUG] Não foi possível deletar arquivo temporário {path}: {pe}"
                        )
                        # Não falha o processamento por causa disso
                    except Exception as e:
                        print(f"[DEBUG] Erro ao deletar arquivo temporário {path}: {e}")
                        # Não falha o processamento por causa disso
        progress_importacao.value = 100
        if resultados:
            state["arquivos"] = resultados
            state["idx_preview"] = 0
            # Atualizar lista de arquivos no tabulator
            atualizar_lista_arquivos()
            atualizar_preview()
            resumo.object = f"{len(resultados)} arquivo(s) processado(s) com sucesso."
            _notify(
                "success",
                f"{len(resultados)} arquivo(s) processado(s) e normalizado(s).",
            )
        else:
            state["arquivos"] = []
            state["idx_preview"] = 0
            preview.value = pd.DataFrame()
            info.object = ""
            resumo.object = "Nenhum arquivo processado com sucesso."
        progress_importacao.visible = False
        btn_processar.name = "Processar e Normalizar"
        btn_processar.button_type = "primary"
        btn_processar.disabled = False

    def atualizar_preview(idx=None):
        if idx is not None:
            # Garantir que idx é um inteiro
            try:
                state["idx_preview"] = int(idx)
            except (ValueError, TypeError):
                state["idx_preview"] = 0
        arquivos = state.get("arquivos", [])
        if not arquivos:
            preview.value = pd.DataFrame()
            info.object = ""
            return
        idx = state["idx_preview"]
        if idx < 0 or idx >= len(arquivos):
            idx = 0
            state["idx_preview"] = idx
        arq = arquivos[idx]
        header_info = f"- Linha de cabeçalho detectada no arquivo: **{arq['idx']+1}**"
        tr_list = [f"- **{k}** → **{v}**" for k, v in arq["transf"].items()]
        info.object = (
            f"**Arquivo:** `{arq['arquivo']}`\n{header_info}\n\n**Transformações Aplicadas:**\n"
            + "\n".join(tr_list)
        )
        preview_df = preparar_para_tabulator(arq["df"])
        preview.value = preview_df.head(200)

    # Tabulator para mostrar todos os arquivos processados
    arquivos_tabulator = pn.widgets.Tabulator(
        value=pd.DataFrame(columns=["#", "Arquivo", "Linhas", "Status"]),
        pagination="remote",
        page_size=10,
        sizing_mode="stretch_width",
        height=150,
        selection=[0] if state.get("arquivos") else [],
        selectable="checkbox",
    )

    btn_refresh_preview = pn.widgets.Button(
        name="🔄 Atualizar Preview", button_type="light", width=150
    )

    def atualizar_lista_arquivos():
        """Atualiza o tabulator com a lista de arquivos processados"""
        arquivos = state.get("arquivos", [])
        if not arquivos:
            arquivos_tabulator.value = pd.DataFrame(
                columns=["#", "Arquivo", "Linhas", "Status"]
            )
            return

        dados = []
        for i, arq in enumerate(arquivos):
            dados.append(
                {
                    "#": i + 1,
                    "Arquivo": arq["arquivo"],
                    "Linhas": len(arq["df"]),
                    "Status": "Processado",
                }
            )

        arquivos_df = pd.DataFrame(dados)
        arquivos_tabulator.value = arquivos_df

        # Selecionar o primeiro arquivo automaticamente
        if not arquivos_tabulator.selection:
            arquivos_tabulator.selection = [0]

    def on_arquivo_selected(event):
        """Quando selecionar um arquivo no tabulator"""
        if event.new and len(event.new) > 0:
            idx = event.new[0]  # Primeiro item selecionado
            atualizar_preview(idx)

    def on_refresh_preview(_):
        """Força atualização do preview do arquivo selecionado"""
        if arquivos_tabulator.selection:
            idx = arquivos_tabulator.selection[0]
            atualizar_preview(idx)
        else:
            _notify("warning", "Selecione um arquivo primeiro")

    arquivos_tabulator.param.watch(on_arquivo_selected, "selection")
    btn_refresh_preview.on_click(on_refresh_preview)

    def on_gravar(_=None):
        arquivos = state.get("arquivos", [])
        if not arquivos:
            return _notify("warning", "Processe um ou mais arquivos primeiro.")
        if not cliente_select.value or not ec_select.value:
            return _notify("warning", "Selecione Cliente e EC.")

        print(f"[DEBUG] 📁 TOTAL DE ARQUIVOS A PROCESSAR: {len(arquivos)}")
        for i, arq in enumerate(arquivos):
            arquivo_nome = arq.get("arquivo", "sem_nome")
            df_shape = (
                arq["df"].shape
                if "df" in arq and hasattr(arq["df"], "shape")
                else "N/A"
            )
            print(
                f"[DEBUG] 📄 Arquivo {i+1}: {arquivo_nome} - DataFrame shape: {df_shape}"
            )

        resultados = []
        processamentoid = state.get("processamentoid")
        from proc.proc_importacao import classificar_e_gravar_recebiveis

        tipo_arquivo = tipo_select.value
        for arq in arquivos:
            try:
                if tipo_arquivo == "R":
                    result = classificar_e_gravar_recebiveis(
                        engine,
                        arq["df"],
                        cliente_id=int(cliente_select.value),
                        ec_id=ec_select.value,  # ec_id agora é VARCHAR, não INT
                        contexto=(contexto_select.value or ""),
                        usuario=usuario_logado or "desconhecido",
                        arquivo_origem=(arq["arquivo"] or ""),
                        processamentoid=arq.get("processamentoid", processamentoid),
                    )
                else:
                    result = classificar_e_gravar_vendas(
                        engine,
                        arq["df"],
                        cliente_id=int(cliente_select.value),
                        ec_id=ec_select.value,  # ec_id agora é VARCHAR, não INT
                        contexto=(contexto_select.value or ""),
                        usuario=usuario_logado or "desconhecido",
                        arquivo_origem=(arq["arquivo"] or ""),
                        processamentoid=arq.get("processamentoid", processamentoid),
                    )
                resultados.append((arq["arquivo"], result, None))
            except Exception as e:
                resultados.append((arq["arquivo"], None, str(e)))
        # Monta resumo premium
        metrics_rows = []
        for fname, result, err in resultados:
            if err:
                metrics_rows.append(pn.pane.Alert(f"**{fname}**: Erro ao gravar: {err}", alert_type="danger"))
            else:
                p_id = result.get('processamentoid', '-')
                total_val = result.get('total', 0)
                metrics_rows.append(
                    pn.Row(
                        pn.pane.Markdown(f"### {fname}"),
                        premium_metric("Processamento ID", p_id),
                        premium_metric("Total de Linhas", f"{total_val:,}"),
                        premium_metric("Status", "Gravado", color="#238636"),
                        sizing_mode="stretch_width"
                    )
                )
        resumo.objects = metrics_rows
        _notify("success", f"Gravaçāo concluída para {len(arquivos)} arquivo(s).")

    btn_processar.on_click(on_process)
    btn_gravar.on_click(on_gravar)

    # Layout Refatorado (Premium UI)
    header_section = create_glass_card(
        pn.Column(
            pn.Row(cliente_select, ec_select, contexto_select, tipo_select, sizing_mode="stretch_width"),
            pn.Row(continuar_checkbox, processamentoid_select, btn_atualizar_processamentoid, sizing_mode="stretch_width"),
            pn.Row(file_input, btn_processar, btn_gravar, btn_reset, align="end", sizing_mode="stretch_width"),
            progress_importacao,
        ),
        title="📥 Configuração de Importação"
    )

    preview_section = create_glass_card(
        pn.Column(
            arquivos_tabulator,
            pn.Row(btn_refresh_preview, align="end"),
            info,
            preview,
        ),
        title="🔍 Preview dos Dados"
    )

    result_section = create_glass_card(
        resumo,
        title="📊 Resultado da Gravação"
    )

    return pn.Column(
        pn.pane.Markdown("# Importação de Arquivos", css_classes=["premium-header"]),
        header_section,
        pn.Spacer(height=20),
        preview_section,
        pn.Spacer(height=20),
        result_section,
        sizing_mode="stretch_width",
        margin=(10, 20)
    )


def _make_tab_gestao_processamentos(
    engine: Engine, usuario_logado: Optional[str]
) -> pn.viewable.Viewable:
    """Aba para gestão de processamentos - listar e deletar"""

    # Tabulator para mostrar processamentos
    processamentos_tabulator = pn.widgets.Tabulator(
        value=pd.DataFrame(),
        pagination="remote",
        page_size=15,
        sizing_mode="stretch_width",
        height=400,
        selection=[],
        selectable="checkbox",
    )

    # Botões de ação
    btn_atualizar = pn.widgets.Button(
        name="🔄 Atualizar Lista", button_type="primary", width=150
    )

    btn_deletar = pn.widgets.Button(
        name="🗑️ Deletar Selecionado", button_type="danger", width=180
    )

    # Painel de status
    status_pane = pn.pane.Markdown(
        "Clique em **Atualizar Lista** para carregar os processamentos."
    )

    def carregar_processamentos():
        """Carrega a lista de processamentos com detalhes"""
        try:
            from datetime import datetime

            dados = listar_processamentos_detalhado(engine)

            if not dados:
                processamentos_tabulator.value = pd.DataFrame(
                    columns=[
                        "ProcessamentoID",
                        "Processadas",
                        "Filtradas",
                        "Total",
                        "Primeira Data",
                        "Última Data",
                    ]
                )
                status_pane.object = "⚠️ **Nenhum processamento encontrado.**"
                return

            # Preparar DataFrame
            df_dados = []
            for item in dados:
                # Converter datas de string para datetime se necessário
                primeira_data = item["primeira_data"]
                if primeira_data and isinstance(primeira_data, str):
                    try:
                        primeira_data = datetime.strptime(
                            primeira_data, "%Y-%m-%d %H:%M:%S"
                        )
                    except:
                        primeira_data = None

                ultima_data = item["ultima_data"]
                if ultima_data and isinstance(ultima_data, str):
                    try:
                        ultima_data = datetime.strptime(
                            ultima_data, "%Y-%m-%d %H:%M:%S"
                        )
                    except:
                        ultima_data = None

                df_dados.append(
                    {
                        "ProcessamentoID": item["processamentoid"],
                        "Processadas": item["qtd_processadas"],
                        "Filtradas": item["qtd_filtradas"],
                        "Total": item["total_linhas"],
                        "Primeira Data": (
                            primeira_data.strftime("%d/%m/%Y %H:%M")
                            if primeira_data
                            else "-"
                        ),
                        "Última Data": (
                            ultima_data.strftime("%d/%m/%Y %H:%M")
                            if ultima_data
                            else "-"
                        ),
                    }
                )

            processamentos_df = pd.DataFrame(df_dados)
            processamentos_tabulator.value = processamentos_df

            total_processamentos = len(dados)
            total_linhas = sum(item["total_linhas"] for item in dados)
            status_pane.object = f"✅ **{total_processamentos} processamento(s)** carregado(s). **Total de {total_linhas:,} linha(s)** no banco."

        except Exception as e:
            status_pane.object = f"❌ **Erro ao carregar processamentos:** {e}"
            _notify("error", f"Erro ao carregar: {e}")

    def deletar_processamento_selecionado():
        """Deleta o processamento selecionado"""
        if not processamentos_tabulator.selection:
            _notify("warning", "Selecione um ou mais processamentos.")
            return

        try:
            df = processamentos_tabulator.value
            idxs = processamentos_tabulator.selection
            ids_linhas = [
                (df.iloc[idx]["ProcessamentoID"], df.iloc[idx]["Total"]) for idx in idxs
            ]

            # Confirmação em lote
            if not hasattr(pn.state, "_confirm_delete"):
                ids_str = ", ".join(str(pid) for pid, _ in ids_linhas)
                total_linhas = sum(tot for _, tot in ids_linhas)
                status_pane.object = f"⚠️ **ATENÇÃO:** Vai deletar ProcessamentoID(s) **{ids_str}** (total {total_linhas} linhas). Clique **Deletar** novamente para confirmar."
                pn.state._confirm_delete = set(pid for pid, _ in ids_linhas)
                return

            # Se já confirmou, executar deleção em lote
            confirmados = pn.state._confirm_delete
            total_deletadas = 0
            detalhes = []
            for processamentoid, _ in ids_linhas:
                if processamentoid in confirmados:
                    resultado = deletar_processamento(engine, processamentoid)
                    total = (
                        resultado["vendas_processadas"] + resultado["vendas_filtradas"]
                    )
                    total_deletadas += total
                    detalhes.append(
                        f"{processamentoid}: {total} linhas ({resultado['vendas_processadas']} processadas + {resultado['vendas_filtradas']} filtradas)"
                    )
            delattr(pn.state, "_confirm_delete")
            status_pane.object = (
                f"✅ **ProcessamentoID(s) deletado(s)!** {total_deletadas} linha(s) removidas.\n"
                + "\n".join(detalhes)
            )
            _notify("success", f"Processamento(s) deletado(s) com sucesso!")
            carregar_processamentos()

        except Exception as e:
            if hasattr(pn.state, "_confirm_delete"):
                delattr(pn.state, "_confirm_delete")
            status_pane.object = f"❌ **Erro ao deletar:** {e}"
            _notify("error", f"Erro ao deletar: {e}")

    # Eventos dos botões
    btn_atualizar.on_click(lambda _: carregar_processamentos())
    btn_deletar.on_click(lambda _: deletar_processamento_selecionado())

    # Layout da aba
    return pn.Column(
        pn.pane.Markdown("# Gestão de Processamentos", css_classes=["premium-header"]),
        create_glass_card(
            pn.Column(
                pn.Row(btn_atualizar, btn_deletar, align="start"),
                status_pane,
                pn.layout.Divider(),
                processamentos_tabulator,
            ),
            title="🗂️ Histórico de Cargas"
        ),
        sizing_mode="stretch_width",
        margin=(10, 20)
    )


def make_importacao_view(
    engine: Engine, usuario_logado: Optional[str]
) -> pn.viewable.Viewable:
    return pn.Tabs(
        ("Importar Arquivo", _make_tab_importar(engine, usuario_logado)),
        ("De-Para de Colunas", _make_tab_depara(engine, usuario_logado)),
        (
            "Gestão de Processamentos",
            _make_tab_gestao_processamentos(engine, usuario_logado),
        ),
        tabs_location="above",
        sizing_mode="stretch_both",
    )
