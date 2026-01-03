"""
Módulo de Interface para Correção de Importações
Permite modificar dados já importados: atualizar ou remover formas de pagamento e bandeiras
"""

import panel as pn
from typing import Optional
from sqlalchemy.engine import Engine

from conf.funcoesbd import (
    listar_processamentos_detalhado,
    listar_valores_unicos_processamento,
    atualizar_forma_pagamento_processamento,
    atualizar_bandeira_processamento,
    remover_linhas_forma_pagamento,
    remover_linhas_bandeira,
    listar_historico_correcoes,
    listar_resumo_processamento,
    listar_resumo_recebiveis_processamento,
    atualizar_lancamento_recebiveis_processamento,
    remover_linhas_lancamento_recebiveis,
    atualizar_status_processamento,
    remover_linhas_status,
)


def criar_ui_correcao(engine: Engine, usuario_atual: str = "sistema") -> pn.Column:
    """
    Cria interface para correção de dados importados.

    Args:
        engine: Engine do SQLAlchemy
        usuario_atual: Nome do usuário logado

    Returns:
        pn.Column com a interface completa
    """

    # ========== Widgets de Seleção ==========

    # Seletor de processamento
    select_processamento = pn.widgets.Select(
        name="Processamento", options={}, width=400, size=10
    )

    # Botões de controle principal
    btn_carregar = pn.widgets.Button(
        name="🔄 Carregar Processamentos", button_type="primary", width=200
    )

    btn_ver_historico = pn.widgets.Button(
        name="📜 Ver Histórico", button_type="primary", width=200
    )

    btn_refresh = pn.widgets.Button(
        name="🔄 Atualizar Resumo", button_type="success", width=200
    )

    # ========== FORMAS DE PAGAMENTO ==========
    # Campos para atualização
    text_nova_forma = pn.widgets.TextInput(
        name="Novo Nome", placeholder="Digite o novo nome...", width=250
    )

    # Botões de ação para Formas de Pagamento
    btn_atualizar_formas = pn.widgets.Button(
        name="✏️ Atualizar Selecionadas",
        button_type="warning",
        width=200,
        disabled=True,
    )

    btn_remover_formas = pn.widgets.Button(
        name="🗑️ Remover Selecionadas", button_type="danger", width=200, disabled=True
    )

    # ========== BANDEIRAS ==========
    # Campos para atualização
    text_nova_bandeira = pn.widgets.TextInput(
        name="Novo Nome", placeholder="Digite o novo nome...", width=250
    )

    # Botões de ação para Bandeiras
    btn_atualizar_bandeiras = pn.widgets.Button(
        name="✏️ Atualizar Selecionadas",
        button_type="warning",
        width=200,
        disabled=True,
    )

    btn_remover_bandeiras = pn.widgets.Button(
        name="🗑️ Remover Selecionadas", button_type="danger", width=200, disabled=True
    )

    # Área de mensagens
    pane_mensagens = pn.pane.Markdown(
        "**Instruções:**\n"
        "1. Carregue a lista de processamentos\n"
        "2. Selecione um processamento (verá o resumo de formas de pagamento e bandeiras)\n"
        "3. **Marque os checkboxes** das linhas que deseja modificar\n"
        "4. Para **Atualizar**: Digite o novo nome e clique em 'Atualizar Selecionadas'\n"
        "5. Para **Remover**: Clique em 'Remover Selecionadas' (move para vendas_filtradas)\n\n"
        "**Nota:** Após cada operação, o resumo é atualizado automaticamente.",
        width=600,
    )

    # Tabulator para histórico
    tabulator_historico = pn.widgets.Tabulator(
        value=None,
        show_index=False,
        pagination="local",
        page_size=20,
        sizing_mode="stretch_width",
        height=400,
        disabled=True,
    )

    # Tabulators para mostrar resumo do processamento COM CHECKBOXES
    tabulator_formas_pagamento = pn.widgets.Tabulator(
        value=None,
        show_index=False,
        sizing_mode="stretch_width",
        height=350,
        disabled=False,
        selectable="checkbox",  # ✅ Habilita checkboxes
        titles={
            "valor": "Forma de Pagamento",
            "quantidade": "Quantidade",
            "valor_total": "Valor Total",
        },
        buttons={
            "quantidade": '<i class="fa fa-hashtag"></i>',
            "valor_total": '<i class="fa fa-dollar"></i>',
        },
    )

    tabulator_bandeiras = pn.widgets.Tabulator(
        value=None,
        show_index=False,
        sizing_mode="stretch_width",
        height=350,
        disabled=False,
        selectable="checkbox",  # ✅ Habilita checkboxes
        titles={
            "valor": "Bandeira",
            "quantidade": "Quantidade",
            "valor_total": "Valor Total",
        },
        buttons={
            "quantidade": '<i class="fa fa-hashtag"></i>',
            "valor_total": '<i class="fa fa-dollar"></i>',
        },
    )

    # ========== RECEBÍVEIS ==========
    # Campos para atualização de lançamentos
    text_novo_lancamento = pn.widgets.TextInput(
        name="Novo Nome", placeholder="Digite o novo nome...", width=250
    )

    # Botões de ação para Recebíveis
    btn_atualizar_lancamentos = pn.widgets.Button(
        name="✏️ Atualizar Selecionados",
        button_type="warning",
        width=200,
        disabled=True,
    )

    btn_remover_lancamentos = pn.widgets.Button(
        name="🗑️ Remover Selecionados", button_type="danger", width=200, disabled=True
    )

    # Tabulator para lançamentos de recebíveis
    tabulator_lancamentos = pn.widgets.Tabulator(
        value=None,
        show_index=False,
        sizing_mode="stretch_width",
        height=350,
        disabled=False,
        selectable="checkbox",  # ✅ Habilita checkboxes
        titles={
            "valor": "Tipo de Lançamento",
            "quantidade": "Quantidade",
            "valor_total": "Valor Total",
        },
        buttons={
            "quantidade": '<i class="fa fa-hashtag"></i>',
            "valor_total": '<i class="fa fa-dollar"></i>',
        },
    )

    # ========== STATUS ==========
    # Campos para atualização
    text_novo_status = pn.widgets.TextInput(
        name="Novo Nome", placeholder="Digite o novo nome...", width=250
    )

    # Botões de ação para Status
    btn_atualizar_status = pn.widgets.Button(
        name="✏️ Atualizar Selecionados",
        button_type="warning",
        width=200,
        disabled=True,
    )

    btn_remover_status = pn.widgets.Button(
        name="🗑️ Remover Selecionados", button_type="danger", width=200, disabled=True
    )

    # Tabulator para status de vendas
    tabulator_status = pn.widgets.Tabulator(
        value=None,
        show_index=False,
        sizing_mode="stretch_width",
        height=350,
        disabled=False,
        selectable="checkbox",  # ✅ Habilita checkboxes
        titles={
            "valor": "Status da Venda",
            "quantidade": "Quantidade",
            "valor_total": "Valor Total",
        },
        buttons={
            "quantidade": '<i class="fa fa-hashtag"></i>',
            "valor_total": '<i class="fa fa-dollar"></i>',
        },
    )

    # ========== Funções de Callback ==========

    def carregar_processamentos(event):
        """Carrega lista de processamentos disponíveis"""
        try:
            pane_mensagens.object = "🔄 Carregando processamentos..."

            processamentos = listar_processamentos_detalhado(engine)

            if not processamentos:
                pane_mensagens.object = "⚠️ Nenhum processamento encontrado."
                return

            # Criar dict {label: processamentoid}
            opcoes = {}
            for p in processamentos:
                pid = p.get("processamentoid", "")
                cliente = p.get("cliente_id", "")
                ec = p.get("ec_id", "")
                data = p.get("data_processamento", "")
                label = f"{pid} - {cliente}/{ec} ({data})"
                opcoes[label] = pid

            select_processamento.options = opcoes

            pane_mensagens.object = f"✅ {len(processamentos)} processamentos carregados. Selecione um para continuar."

            # ✅ Notificação de sucesso
            try:
                pn.state.notifications.success(
                    f"✅ {len(processamentos)} processamentos carregados.",
                    duration=3000,
                )
            except Exception:
                pass

        except Exception as e:
            pane_mensagens.object = f"❌ Erro ao carregar processamentos: {str(e)}"

            # ❌ Notificação de erro
            try:
                pn.state.notifications.error(
                    f"❌ Erro ao carregar processamentos.", duration=5000
                )
            except Exception:
                pass

    def on_processamento_change(event):
        """Quando o usuário seleciona um processamento, carrega o resumo"""
        if not select_processamento.value:
            tabulator_formas_pagamento.value = None
            tabulator_bandeiras.value = None
            tabulator_lancamentos.value = None
            tabulator_status.value = None
            btn_atualizar_formas.disabled = True
            btn_remover_formas.disabled = True
            btn_atualizar_bandeiras.disabled = True
            btn_remover_bandeiras.disabled = True
            btn_atualizar_lancamentos.disabled = True
            btn_remover_lancamentos.disabled = True
            btn_atualizar_status.disabled = True
            btn_remover_status.disabled = True
            return

        try:
            pane_mensagens.object = "🔍 Carregando resumo do processamento..."
            atualizar_resumo_processamento()
            pane_mensagens.object = (
                "✅ Resumo carregado! Marque os checkboxes para selecionar itens."
            )

            try:
                pn.state.notifications.success("✅ Resumo carregado!", duration=3000)
            except Exception:
                pass

        except Exception as e:
            pane_mensagens.object = f"❌ Erro ao carregar resumo: {str(e)}"
            try:
                pn.state.notifications.error(
                    f"❌ Erro ao carregar resumo", duration=5000
                )
            except Exception:
                pass

    def atualizar_resumo_processamento():
        """Atualiza os tabulators com resumo de formas de pagamento, bandeiras, recebíveis e status"""
        if not select_processamento.value:
            tabulator_formas_pagamento.value = None
            tabulator_bandeiras.value = None
            tabulator_lancamentos.value = None
            tabulator_status.value = None
            return

        try:
            import pandas as pd

            processamentoid = select_processamento.value

            # Resumo de vendas
            resumo = listar_resumo_processamento(engine, processamentoid)

            # Atualizar tabulator de formas de pagamento
            if resumo["formas_pagamento"]:
                df_formas = pd.DataFrame(resumo["formas_pagamento"])
                # Formatar valor_total como moeda
                if "valor_total" in df_formas.columns:
                    df_formas["valor_total"] = df_formas["valor_total"].apply(
                        lambda x: f"R$ {x:,.2f}" if pd.notna(x) else "R$ 0,00"
                    )
                tabulator_formas_pagamento.value = df_formas
            else:
                tabulator_formas_pagamento.value = None

            # Atualizar tabulator de bandeiras
            if resumo["bandeiras"]:
                df_bandeiras = pd.DataFrame(resumo["bandeiras"])
                # Formatar valor_total como moeda
                if "valor_total" in df_bandeiras.columns:
                    df_bandeiras["valor_total"] = df_bandeiras["valor_total"].apply(
                        lambda x: f"R$ {x:,.2f}" if pd.notna(x) else "R$ 0,00"
                    )
                tabulator_bandeiras.value = df_bandeiras
            else:
                tabulator_bandeiras.value = None

            # Atualizar tabulator de status
            if resumo.get("status"):
                df_status = pd.DataFrame(resumo["status"])
                # Formatar valor_total como moeda
                if "valor_total" in df_status.columns:
                    df_status["valor_total"] = df_status["valor_total"].apply(
                        lambda x: f"R$ {x:,.2f}" if pd.notna(x) else "R$ 0,00"
                    )
                tabulator_status.value = df_status
            else:
                tabulator_status.value = None

            # Resumo de recebíveis
            resumo_recebiveis = listar_resumo_recebiveis_processamento(
                engine, processamentoid
            )

            # Atualizar tabulator de lançamentos de recebíveis
            if resumo_recebiveis["lancamentos"]:
                df_lancamentos = pd.DataFrame(resumo_recebiveis["lancamentos"])
                # Formatar valor_total como moeda
                if "valor_total" in df_lancamentos.columns:
                    df_lancamentos["valor_total"] = df_lancamentos["valor_total"].apply(
                        lambda x: f"R$ {x:,.2f}" if pd.notna(x) else "R$ 0,00"
                    )
                tabulator_lancamentos.value = df_lancamentos
            else:
                tabulator_lancamentos.value = None

        except Exception as e:
            print(f"[ERROR] Erro ao atualizar resumo: {e}")

    def atualizar_formas_pagamento(event):
        """Atualiza as formas de pagamento selecionadas"""
        if not select_processamento.value:
            pane_mensagens.object = "⚠️ Selecione um processamento primeiro."
            return

        selecionadas = tabulator_formas_pagamento.selection
        if not selecionadas:
            pane_mensagens.object = (
                "⚠️ Marque os checkboxes das formas de pagamento que deseja atualizar."
            )
            try:
                pn.state.notifications.warning(
                    "⚠️ Nenhuma forma de pagamento selecionada.", duration=3000
                )
            except Exception:
                pass
            return

        novo_valor = text_nova_forma.value
        if not novo_valor or not novo_valor.strip():
            pane_mensagens.object = "⚠️ Digite o novo nome para Forma de Pagamento."
            try:
                pn.state.notifications.warning(
                    "⚠️ Digite o novo nome primeiro.", duration=3000
                )
            except Exception:
                pass
            return

        processamentoid = select_processamento.value

        try:
            btn_atualizar_formas.disabled = True
            btn_atualizar_formas.name = "⏳ Processando..."

            total_linhas = 0
            for idx in selecionadas:
                valor_antigo = tabulator_formas_pagamento.value.iloc[idx]["valor"]
                pane_mensagens.object = (
                    f"🔄 Atualizando '{valor_antigo}' para '{novo_valor}'..."
                )

                sucesso, msg, linhas = atualizar_forma_pagamento_processamento(
                    engine, processamentoid, valor_antigo, novo_valor, usuario_atual
                )

                if sucesso:
                    total_linhas += linhas
                else:
                    pane_mensagens.object = f"❌ Erro: {msg}"
                    try:
                        pn.state.notifications.error(f"❌ {msg[:100]}", duration=7000)
                    except Exception:
                        pass
                    return

            pane_mensagens.object = f"✅ **{len(selecionadas)} formas de pagamento atualizadas**\n\n**{total_linhas} linhas afetadas**"

            try:
                pn.state.notifications.success(
                    f"✅ {total_linhas} linhas atualizadas!", duration=5000
                )
            except Exception:
                pass

            # ✅ Recarregar resumo
            atualizar_resumo_processamento()
            text_nova_forma.value = ""  # Limpar campo

        except Exception as e:
            pane_mensagens.object = f"❌ Erro inesperado: {str(e)}"
            try:
                pn.state.notifications.error(f"❌ Erro crítico", duration=7000)
            except Exception:
                pass
        finally:
            btn_atualizar_formas.disabled = False
            btn_atualizar_formas.name = "✏️ Atualizar Selecionadas"

    def remover_formas_pagamento(event):
        """Remove as formas de pagamento selecionadas"""
        if not select_processamento.value:
            pane_mensagens.object = "⚠️ Selecione um processamento primeiro."
            return

        selecionadas = tabulator_formas_pagamento.selection
        if not selecionadas:
            pane_mensagens.object = (
                "⚠️ Marque os checkboxes das formas de pagamento que deseja remover."
            )
            try:
                pn.state.notifications.warning(
                    "⚠️ Nenhuma forma de pagamento selecionada.", duration=3000
                )
            except Exception:
                pass
            return

        processamentoid = select_processamento.value

        try:
            btn_remover_formas.disabled = True
            btn_remover_formas.name = "⏳ Processando..."

            total_linhas = 0
            for idx in selecionadas:
                valor = tabulator_formas_pagamento.value.iloc[idx]["valor"]
                pane_mensagens.object = f"🗑️ Removendo '{valor}'..."

                sucesso, msg, linhas = remover_linhas_forma_pagamento(
                    engine, processamentoid, valor, usuario_atual
                )

                if sucesso:
                    total_linhas += linhas
                else:
                    pane_mensagens.object = f"❌ Erro: {msg}"
                    try:
                        pn.state.notifications.error(f"❌ {msg[:100]}", duration=7000)
                    except Exception:
                        pass
                    return

            pane_mensagens.object = f"✅ **{len(selecionadas)} formas de pagamento removidas**\n\n**{total_linhas} linhas movidas para vendas_filtradas**"

            try:
                pn.state.notifications.success(
                    f"✅ {total_linhas} linhas removidas!", duration=5000
                )
            except Exception:
                pass

            # ✅ Recarregar resumo
            atualizar_resumo_processamento()

        except Exception as e:
            pane_mensagens.object = f"❌ Erro inesperado: {str(e)}"
            try:
                pn.state.notifications.error(f"❌ Erro crítico", duration=7000)
            except Exception:
                pass
        finally:
            btn_remover_formas.disabled = False
            btn_remover_formas.name = "🗑️ Remover Selecionadas"

    def atualizar_bandeiras(event):
        """Atualiza as bandeiras selecionadas"""
        if not select_processamento.value:
            pane_mensagens.object = "⚠️ Selecione um processamento primeiro."
            return

        selecionadas = tabulator_bandeiras.selection
        if not selecionadas:
            pane_mensagens.object = (
                "⚠️ Marque os checkboxes das bandeiras que deseja atualizar."
            )
            try:
                pn.state.notifications.warning(
                    "⚠️ Nenhuma bandeira selecionada.", duration=3000
                )
            except Exception:
                pass
            return

        novo_valor = text_nova_bandeira.value
        if not novo_valor or not novo_valor.strip():
            pane_mensagens.object = "⚠️ Digite o novo nome para Bandeira."
            try:
                pn.state.notifications.warning(
                    "⚠️ Digite o novo nome primeiro.", duration=3000
                )
            except Exception:
                pass
            return

        processamentoid = select_processamento.value

        try:
            btn_atualizar_bandeiras.disabled = True
            btn_atualizar_bandeiras.name = "⏳ Processando..."

            total_linhas = 0
            for idx in selecionadas:
                valor_antigo = tabulator_bandeiras.value.iloc[idx]["valor"]
                pane_mensagens.object = (
                    f"🔄 Atualizando '{valor_antigo}' para '{novo_valor}'..."
                )

                sucesso, msg, linhas = atualizar_bandeira_processamento(
                    engine, processamentoid, valor_antigo, novo_valor, usuario_atual
                )

                if sucesso:
                    total_linhas += linhas
                else:
                    pane_mensagens.object = f"❌ Erro: {msg}"
                    try:
                        pn.state.notifications.error(f"❌ {msg[:100]}", duration=7000)
                    except Exception:
                        pass
                    return

            pane_mensagens.object = f"✅ **{len(selecionadas)} bandeiras atualizadas**\n\n**{total_linhas} linhas afetadas**"

            try:
                pn.state.notifications.success(
                    f"✅ {total_linhas} linhas atualizadas!", duration=5000
                )
            except Exception:
                pass

            # ✅ Recarregar resumo
            atualizar_resumo_processamento()
            text_nova_bandeira.value = ""  # Limpar campo

        except Exception as e:
            pane_mensagens.object = f"❌ Erro inesperado: {str(e)}"
            try:
                pn.state.notifications.error(f"❌ Erro crítico", duration=7000)
            except Exception:
                pass
        finally:
            btn_atualizar_bandeiras.disabled = False
            btn_atualizar_bandeiras.name = "✏️ Atualizar Selecionadas"

    def remover_bandeiras(event):
        """Remove as bandeiras selecionadas"""
        if not select_processamento.value:
            pane_mensagens.object = "⚠️ Selecione um processamento primeiro."
            return

        selecionadas = tabulator_bandeiras.selection
        if not selecionadas:
            pane_mensagens.object = (
                "⚠️ Marque os checkboxes das bandeiras que deseja remover."
            )
            try:
                pn.state.notifications.warning(
                    "⚠️ Nenhuma bandeira selecionada.", duration=3000
                )
            except Exception:
                pass
            return

        processamentoid = select_processamento.value

        try:
            btn_remover_bandeiras.disabled = True
            btn_remover_bandeiras.name = "⏳ Processando..."

            total_linhas = 0
            for idx in selecionadas:
                valor = tabulator_bandeiras.value.iloc[idx]["valor"]
                pane_mensagens.object = f"🗑️ Removendo '{valor}'..."

                sucesso, msg, linhas = remover_linhas_bandeira(
                    engine, processamentoid, valor, usuario_atual
                )

                if sucesso:
                    total_linhas += linhas
                else:
                    pane_mensagens.object = f"❌ Erro: {msg}"
                    try:
                        pn.state.notifications.error(f"❌ {msg[:100]}", duration=7000)
                    except Exception:
                        pass
                    return

            pane_mensagens.object = f"✅ **{len(selecionadas)} bandeiras removidas**\n\n**{total_linhas} linhas movidas para vendas_filtradas**"

            try:
                pn.state.notifications.success(
                    f"✅ {total_linhas} linhas removidas!", duration=5000
                )
            except Exception:
                pass

            # ✅ Recarregar resumo
            atualizar_resumo_processamento()

        except Exception as e:
            pane_mensagens.object = f"❌ Erro inesperado: {str(e)}"
            try:
                pn.state.notifications.error(f"❌ Erro crítico", duration=7000)
            except Exception:
                pass
        finally:
            btn_remover_bandeiras.disabled = False
            btn_remover_bandeiras.name = "🗑️ Remover Selecionadas"

    def atualizar_lancamentos_recebiveis(event):
        """Atualiza os lançamentos de recebíveis selecionados"""
        if not select_processamento.value:
            pane_mensagens.object = "⚠️ Selecione um processamento primeiro."
            return

        selecionadas = tabulator_lancamentos.selection
        if not selecionadas:
            pane_mensagens.object = (
                "⚠️ Marque os checkboxes dos lançamentos que deseja atualizar."
            )
            try:
                pn.state.notifications.warning(
                    "⚠️ Nenhum lançamento selecionado.", duration=3000
                )
            except Exception:
                pass
            return

        novo_valor = text_novo_lancamento.value
        if not novo_valor or not novo_valor.strip():
            pane_mensagens.object = "⚠️ Digite o novo nome para o Lançamento."
            try:
                pn.state.notifications.warning(
                    "⚠️ Digite o novo nome primeiro.", duration=3000
                )
            except Exception:
                pass
            return

        processamentoid = select_processamento.value

        try:
            btn_atualizar_lancamentos.disabled = True
            btn_atualizar_lancamentos.name = "⏳ Processando..."

            total_linhas = 0
            for idx in selecionadas:
                valor_antigo = tabulator_lancamentos.value.iloc[idx]["valor"]
                pane_mensagens.object = (
                    f"🔄 Atualizando '{valor_antigo}' para '{novo_valor}'..."
                )

                sucesso, msg, linhas = atualizar_lancamento_recebiveis_processamento(
                    engine, processamentoid, valor_antigo, novo_valor, usuario_atual
                )

                if sucesso:
                    total_linhas += linhas
                else:
                    pane_mensagens.object = f"❌ Erro: {msg}"
                    try:
                        pn.state.notifications.error(f"❌ {msg[:100]}", duration=7000)
                    except Exception:
                        pass
                    return

            pane_mensagens.object = f"✅ **{len(selecionadas)} lançamentos atualizados**\n\n**{total_linhas} linhas afetadas**"

            try:
                pn.state.notifications.success(
                    f"✅ {total_linhas} linhas atualizadas!", duration=5000
                )
            except Exception:
                pass

            # ✅ Recarregar resumo
            atualizar_resumo_processamento()
            text_novo_lancamento.value = ""  # Limpar campo

        except Exception as e:
            pane_mensagens.object = f"❌ Erro inesperado: {str(e)}"
            try:
                pn.state.notifications.error(f"❌ Erro crítico", duration=7000)
            except Exception:
                pass
        finally:
            btn_atualizar_lancamentos.disabled = False
            btn_atualizar_lancamentos.name = "✏️ Atualizar Selecionados"

    def remover_lancamentos_recebiveis(event):
        """Remove os lançamentos de recebíveis selecionados"""
        if not select_processamento.value:
            pane_mensagens.object = "⚠️ Selecione um processamento primeiro."
            return

        selecionadas = tabulator_lancamentos.selection
        if not selecionadas:
            pane_mensagens.object = (
                "⚠️ Marque os checkboxes dos lançamentos que deseja remover."
            )
            try:
                pn.state.notifications.warning(
                    "⚠️ Nenhum lançamento selecionado.", duration=3000
                )
            except Exception:
                pass
            return

        processamentoid = select_processamento.value

        try:
            btn_remover_lancamentos.disabled = True
            btn_remover_lancamentos.name = "⏳ Processando..."

            total_linhas = 0
            for idx in selecionadas:
                valor = tabulator_lancamentos.value.iloc[idx]["valor"]
                pane_mensagens.object = f"🗑️ Removendo '{valor}'..."

                sucesso, msg, linhas = remover_linhas_lancamento_recebiveis(
                    engine, processamentoid, valor, usuario_atual
                )

                if sucesso:
                    total_linhas += linhas
                else:
                    pane_mensagens.object = f"❌ Erro: {msg}"
                    try:
                        pn.state.notifications.error(f"❌ {msg[:100]}", duration=7000)
                    except Exception:
                        pass
                    return

            pane_mensagens.object = f"✅ **{len(selecionadas)} lançamentos removidos**\n\n**{total_linhas} linhas movidas para recebiveis_filtrados**"

            try:
                pn.state.notifications.success(
                    f"✅ {total_linhas} linhas removidas!", duration=5000
                )
            except Exception:
                pass

            # ✅ Recarregar resumo
            atualizar_resumo_processamento()

        except Exception as e:
            pane_mensagens.object = f"❌ Erro inesperado: {str(e)}"
            try:
                pn.state.notifications.error(f"❌ Erro crítico", duration=7000)
            except Exception:
                pass
        finally:
            btn_remover_lancamentos.disabled = False
            btn_remover_lancamentos.name = "🗑️ Remover Selecionados"

    def atualizar_status(event):
        """Atualiza os status selecionados"""
        if not select_processamento.value:
            pane_mensagens.object = "⚠️ Selecione um processamento primeiro."
            return

        selecionadas = tabulator_status.selection
        if not selecionadas:
            pane_mensagens.object = (
                "⚠️ Marque os checkboxes dos status que deseja atualizar."
            )
            try:
                pn.state.notifications.warning(
                    "⚠️ Nenhum status selecionado.", duration=3000
                )
            except Exception:
                pass
            return

        novo_valor = text_novo_status.value
        if not novo_valor or not novo_valor.strip():
            pane_mensagens.object = "⚠️ Digite o novo nome para Status."
            try:
                pn.state.notifications.warning(
                    "⚠️ Campo obrigatório: Novo Nome", duration=3000
                )
            except Exception:
                pass
            return

        processamentoid = select_processamento.value

        try:
            btn_atualizar_status.disabled = True
            btn_atualizar_status.name = "⏳ Processando..."

            total_linhas = 0
            for idx in selecionadas:
                valor_antigo = tabulator_status.value.iloc[idx]["valor"]
                pane_mensagens.object = (
                    f"✏️ Atualizando '{valor_antigo}' para '{novo_valor}'..."
                )

                sucesso, msg, linhas = atualizar_status_processamento(
                    engine, processamentoid, valor_antigo, novo_valor, usuario_atual
                )

                if sucesso:
                    total_linhas += linhas
                else:
                    pane_mensagens.object = f"❌ Erro: {msg}"
                    try:
                        pn.state.notifications.error(f"❌ {msg[:100]}", duration=7000)
                    except Exception:
                        pass
                    return

            pane_mensagens.object = f"✅ **{len(selecionadas)} status atualizados**\n\n**{total_linhas} linhas afetadas**"

            try:
                pn.state.notifications.success(
                    f"✅ {total_linhas} linhas atualizadas!", duration=5000
                )
            except Exception:
                pass

            # ✅ Recarregar resumo
            atualizar_resumo_processamento()
            text_novo_status.value = ""  # Limpar campo

        except Exception as e:
            pane_mensagens.object = f"❌ Erro inesperado: {str(e)}"
            try:
                pn.state.notifications.error(f"❌ Erro crítico", duration=7000)
            except Exception:
                pass
        finally:
            btn_atualizar_status.disabled = False
            btn_atualizar_status.name = "✏️ Atualizar Selecionados"

    def remover_status(event):
        """Remove os status selecionados"""
        if not select_processamento.value:
            pane_mensagens.object = "⚠️ Selecione um processamento primeiro."
            return

        selecionadas = tabulator_status.selection
        if not selecionadas:
            pane_mensagens.object = (
                "⚠️ Marque os checkboxes dos status que deseja remover."
            )
            try:
                pn.state.notifications.warning(
                    "⚠️ Nenhum status selecionado.", duration=3000
                )
            except Exception:
                pass
            return

        processamentoid = select_processamento.value

        try:
            btn_remover_status.disabled = True
            btn_remover_status.name = "⏳ Processando..."

            total_linhas = 0
            for idx in selecionadas:
                valor = tabulator_status.value.iloc[idx]["valor"]
                pane_mensagens.object = f"🗑️ Removendo '{valor}'..."

                sucesso, msg, linhas = remover_linhas_status(
                    engine, processamentoid, valor, usuario_atual
                )

                if sucesso:
                    total_linhas += linhas
                else:
                    pane_mensagens.object = f"❌ Erro: {msg}"
                    try:
                        pn.state.notifications.error(f"❌ {msg[:100]}", duration=7000)
                    except Exception:
                        pass
                    return

            pane_mensagens.object = f"✅ **{len(selecionadas)} status removidos**\n\n**{total_linhas} linhas movidas para vendas_filtradas**"

            try:
                pn.state.notifications.success(
                    f"✅ {total_linhas} linhas removidas!", duration=5000
                )
            except Exception:
                pass

            # ✅ Recarregar resumo
            atualizar_resumo_processamento()

        except Exception as e:
            pane_mensagens.object = f"❌ Erro inesperado: {str(e)}"
            try:
                pn.state.notifications.error(f"❌ Erro crítico", duration=7000)
            except Exception:
                pass
        finally:
            btn_remover_status.disabled = False
            btn_remover_status.name = "🗑️ Remover Selecionados"

    def ver_historico(event):
        """Carrega e exibe histórico de correções"""
        try:
            pane_mensagens.object = "🔍 Carregando histórico de correções..."

            # Buscar histórico (últimos 100 registros)
            historico = listar_historico_correcoes(engine, limite=100)

            if not historico:
                pane_mensagens.object = "ℹ️ Nenhum histórico de correção encontrado. A tabela de log pode não existir ainda."
                tabulator_historico.value = None
                return

            # Converter para DataFrame para exibição
            import pandas as pd

            df = pd.DataFrame(historico)

            # Formatar colunas para melhor visualização
            if "data_correcao" in df.columns:
                df["data_correcao"] = pd.to_datetime(df["data_correcao"]).dt.strftime(
                    "%d/%m/%Y %H:%M"
                )

            # Renomear colunas para português
            df = df.rename(
                columns={
                    "id": "ID",
                    "processamentoid": "Processamento",
                    "tipo_correcao": "Tipo",
                    "valor_antigo": "Valor Antigo",
                    "valor_novo": "Valor Novo",
                    "linhas_afetadas": "Linhas",
                    "usuario": "Usuário",
                    "data_correcao": "Data",
                }
            )

            tabulator_historico.value = df
            pane_mensagens.object = (
                f"✅ {len(historico)} correções encontradas no histórico."
            )

        except Exception as e:
            pane_mensagens.object = f"❌ Erro ao carregar histórico: {str(e)}"
            tabulator_historico.value = None

    def refresh_resumo(event):
        """Atualiza manualmente o resumo do processamento"""
        if not select_processamento.value:
            try:
                pn.state.notifications.warning(
                    "⚠️ Selecione um processamento primeiro.", duration=3000
                )
            except Exception:
                pass
            pane_mensagens.object = (
                "⚠️ Selecione um processamento para atualizar o resumo."
            )
            return

        try:
            pn.state.notifications.info("🔄 Atualizando resumo...", duration=2000)
        except Exception:
            pass

        atualizar_resumo_processamento()

        try:
            pn.state.notifications.success("✅ Resumo atualizado!", duration=3000)
        except Exception:
            pass

    def on_formas_selection_change(event):
        """Habilita/desabilita botões baseado na seleção"""
        tem_selecao = len(tabulator_formas_pagamento.selection) > 0
        btn_atualizar_formas.disabled = not tem_selecao
        btn_remover_formas.disabled = not tem_selecao

    def on_bandeiras_selection_change(event):
        """Habilita/desabilita botões baseado na seleção"""
        tem_selecao = len(tabulator_bandeiras.selection) > 0
        btn_atualizar_bandeiras.disabled = not tem_selecao
        btn_remover_bandeiras.disabled = not tem_selecao

    def on_lancamentos_selection_change(event):
        """Habilita/desabilita botões baseado na seleção"""
        tem_selecao = len(tabulator_lancamentos.selection) > 0
        btn_atualizar_lancamentos.disabled = not tem_selecao
        btn_remover_lancamentos.disabled = not tem_selecao

    def on_status_selection_change(event):
        """Habilita/desabilita botões baseado na seleção"""
        tem_selecao = len(tabulator_status.selection) > 0
        btn_atualizar_status.disabled = not tem_selecao
        btn_remover_status.disabled = not tem_selecao

    # ========== Conectar Callbacks ==========

    btn_carregar.on_click(carregar_processamentos)
    btn_ver_historico.on_click(ver_historico)
    btn_refresh.on_click(refresh_resumo)
    select_processamento.param.watch(on_processamento_change, "value")

    # Callbacks para Formas de Pagamento
    btn_atualizar_formas.on_click(atualizar_formas_pagamento)
    btn_remover_formas.on_click(remover_formas_pagamento)
    tabulator_formas_pagamento.param.watch(on_formas_selection_change, "selection")

    # Callbacks para Bandeiras
    btn_atualizar_bandeiras.on_click(atualizar_bandeiras)
    btn_remover_bandeiras.on_click(remover_bandeiras)
    tabulator_bandeiras.param.watch(on_bandeiras_selection_change, "selection")

    # Callbacks para Recebíveis
    btn_atualizar_lancamentos.on_click(atualizar_lancamentos_recebiveis)
    btn_remover_lancamentos.on_click(remover_lancamentos_recebiveis)
    tabulator_lancamentos.param.watch(on_lancamentos_selection_change, "selection")

    # Callbacks para Status
    btn_atualizar_status.on_click(atualizar_status)
    btn_remover_status.on_click(remover_status)
    tabulator_status.param.watch(on_status_selection_change, "selection")

    # ========== Layout ==========

    layout = pn.Column(
        pn.pane.Markdown("## 🔧 Correção de Importações"),
        pn.pane.Markdown(
            "Esta ferramenta permite corrigir dados já importados. "
            "Você pode atualizar valores ou remover linhas com base em Forma de Pagamento ou Bandeira. "
            "**Importante:** Dados removidos são movidos para `vendas_filtradas`, não deletados permanentemente."
        ),
        pn.layout.Divider(),
        # Seção 1: Seleção de Processamento
        pn.Card(
            pn.Row(
                select_processamento,
                pn.Spacer(width=20),
                pn.Column(btn_carregar, btn_ver_historico),
            ),
            title="📋 1. Selecionar Processamento",
            collapsed=False,
        ),
        # Seção 2: Resumo e Ações
        pn.Card(
            pn.Column(
                pn.Row(pn.Spacer(), btn_refresh),
                pn.layout.Divider(),
                pane_mensagens,
            ),
            title="📊 2. Resumo do Processamento",
            collapsed=False,
        ),
        # Seção 3: Formas de Pagamento
        pn.Card(
            pn.Column(
                pn.pane.Markdown(
                    "**Instruções:** Marque os checkboxes das formas de pagamento que deseja modificar. "
                    "Para atualizar, digite o novo nome e clique em 'Atualizar'. Para remover, clique em 'Remover'."
                ),
                tabulator_formas_pagamento,
                pn.layout.Divider(),
                pn.Row(
                    text_nova_forma,
                    pn.Spacer(width=20),
                    btn_atualizar_formas,
                    pn.Spacer(width=10),
                    btn_remover_formas,
                ),
            ),
            title="💳 3. Formas de Pagamento",
            collapsed=False,
        ),
        # Seção 4: Bandeiras
        pn.Card(
            pn.Column(
                pn.pane.Markdown(
                    "**Instruções:** Marque os checkboxes das bandeiras que deseja modificar. "
                    "Para atualizar, digite o novo nome e clique em 'Atualizar'. Para remover, clique em 'Remover'."
                ),
                tabulator_bandeiras,
                pn.layout.Divider(),
                pn.Row(
                    text_nova_bandeira,
                    pn.Spacer(width=20),
                    btn_atualizar_bandeiras,
                    pn.Spacer(width=10),
                    btn_remover_bandeiras,
                ),
            ),
            title="🏦 4. Bandeiras",
            collapsed=False,
        ),
        # Seção 5: Recebíveis (Lançamentos)
        pn.Card(
            pn.Column(
                pn.pane.Markdown(
                    "**Instruções:** Marque os checkboxes dos tipos de lançamento que deseja modificar. "
                    "Para atualizar, digite o novo nome e clique em 'Atualizar'. Para remover, clique em 'Remover' "
                    "(move para recebiveis_filtrados)."
                ),
                tabulator_lancamentos,
                pn.layout.Divider(),
                pn.Row(
                    text_novo_lancamento,
                    pn.Spacer(width=20),
                    btn_atualizar_lancamentos,
                    pn.Spacer(width=10),
                    btn_remover_lancamentos,
                ),
            ),
            title="📋 5. Recebíveis (Lançamentos)",
            collapsed=False,
        ),
        # Seção 6: Status
        pn.Card(
            pn.Column(
                pn.pane.Markdown(
                    "**Instruções:** Marque os checkboxes dos status que deseja modificar. "
                    "Para atualizar, digite o novo nome e clique em 'Atualizar'. Para remover, clique em 'Remover' "
                    "(move para vendas_filtradas)."
                ),
                tabulator_status,
                pn.layout.Divider(),
                pn.Row(
                    text_novo_status,
                    pn.Spacer(width=20),
                    btn_atualizar_status,
                    pn.Spacer(width=10),
                    btn_remover_status,
                ),
            ),
            title="📊 6. Status",
            collapsed=False,
        ),
        # Seção 7: Histórico de Correções
        pn.Card(
            tabulator_historico, title="📜 7. Histórico de Correções", collapsed=True
        ),
        sizing_mode="stretch_width",
    )

    return layout
