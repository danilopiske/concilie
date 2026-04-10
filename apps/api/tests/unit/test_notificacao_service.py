"""Testes unitários para NotificacaoService."""

from unittest.mock import MagicMock, patch

import pytest

from app.services.notificacao_service import NotificacaoService


def make_db():
    """Cria um mock de Session SQLAlchemy."""
    db = MagicMock()
    return db


def make_notificacao(**kwargs):
    notif = MagicMock()
    notif.id = kwargs.get("id", "uuid-test-1")
    notif.usuario_id = kwargs.get("usuario_id", None)
    notif.tipo = kwargs.get("tipo", "relatorio_ok")
    notif.titulo = kwargs.get("titulo", "Título Teste")
    notif.mensagem = kwargs.get("mensagem", "Mensagem teste")
    notif.link = kwargs.get("link", None)
    notif.lida = kwargs.get("lida", False)
    return notif


class TestCriar:
    def test_criar_notificacao_global(self):
        db = make_db()
        with patch("app.services.notificacao_service.Notificacao") as MockNotif:
            instance = MagicMock()
            MockNotif.return_value = instance
            db.refresh.side_effect = lambda x: None

            result = NotificacaoService.criar(
                db, tipo="relatorio_ok", titulo="OK", mensagem="Concluído"
            )

            db.add.assert_called_once_with(instance)
            db.commit.assert_called_once()
            db.refresh.assert_called_once_with(instance)

    def test_criar_notificacao_com_usuario_id(self):
        db = make_db()
        with patch("app.services.notificacao_service.Notificacao") as MockNotif:
            instance = MagicMock()
            MockNotif.return_value = instance

            NotificacaoService.criar(
                db,
                tipo="importacao_ok",
                titulo="Importação OK",
                mensagem="Arquivo importado",
                usuario_id=42,
                link="/importar/processamentos",
            )

            MockNotif.assert_called_once_with(
                usuario_id=42,
                tipo="importacao_ok",
                titulo="Importação OK",
                mensagem="Arquivo importado",
                link="/importar/processamentos",
            )


class TestListar:
    def test_listar_sem_filtros(self):
        db = make_db()
        query_mock = MagicMock()
        db.query.return_value = query_mock
        query_mock.filter.return_value = query_mock
        query_mock.order_by.return_value = query_mock
        query_mock.offset.return_value = query_mock
        query_mock.limit.return_value = query_mock
        query_mock.all.return_value = []

        result = NotificacaoService.listar(db)

        db.query.assert_called_once()
        assert result == []

    def test_listar_com_lida_false(self):
        db = make_db()
        query_mock = MagicMock()
        db.query.return_value = query_mock
        query_mock.filter.return_value = query_mock
        query_mock.order_by.return_value = query_mock
        query_mock.offset.return_value = query_mock
        query_mock.limit.return_value = query_mock
        notifs = [make_notificacao(lida=False)]
        query_mock.all.return_value = notifs

        result = NotificacaoService.listar(db, lida=False)

        assert result == notifs


class TestContarNaoLidas:
    def test_contar_sem_usuario(self):
        db = make_db()
        query_mock = MagicMock()
        db.query.return_value = query_mock
        query_mock.filter.return_value = query_mock
        query_mock.count.return_value = 3

        result = NotificacaoService.contar_nao_lidas(db)

        assert result == 3

    def test_contar_com_usuario_id(self):
        db = make_db()
        query_mock = MagicMock()
        db.query.return_value = query_mock
        query_mock.filter.return_value = query_mock
        query_mock.count.return_value = 1

        result = NotificacaoService.contar_nao_lidas(db, usuario_id=5)

        assert result == 1
        # filter chamado 2x: uma para lida=False, outra para usuario_id
        assert query_mock.filter.call_count == 2


class TestMarcarLida:
    def test_marcar_lida_existente(self):
        db = make_db()
        notif = make_notificacao(lida=False)
        db.get.return_value = notif

        result = NotificacaoService.marcar_lida(db, "uuid-test-1")

        assert notif.lida is True
        db.commit.assert_called_once()
        db.refresh.assert_called_once_with(notif)

    def test_marcar_lida_nao_encontrada(self):
        db = make_db()
        db.get.return_value = None

        result = NotificacaoService.marcar_lida(db, "nao-existe")

        assert result is None
        db.commit.assert_not_called()


class TestMarcarTodasLidas:
    def test_marcar_todas_sem_usuario(self):
        db = make_db()
        query_mock = MagicMock()
        db.query.return_value = query_mock
        query_mock.filter.return_value = query_mock

        NotificacaoService.marcar_todas_lidas(db)

        query_mock.update.assert_called_once_with({"lida": True}, synchronize_session=False)
        db.commit.assert_called_once()

    def test_marcar_todas_com_usuario_id(self):
        db = make_db()
        query_mock = MagicMock()
        db.query.return_value = query_mock
        query_mock.filter.return_value = query_mock

        NotificacaoService.marcar_todas_lidas(db, usuario_id=7)

        assert query_mock.filter.call_count == 2


class TestRemover:
    def test_remover_existente(self):
        db = make_db()
        notif = make_notificacao()
        db.get.return_value = notif

        result = NotificacaoService.remover(db, "uuid-test-1")

        assert result is True
        db.delete.assert_called_once_with(notif)
        db.commit.assert_called_once()

    def test_remover_nao_encontrada(self):
        db = make_db()
        db.get.return_value = None

        result = NotificacaoService.remover(db, "nao-existe")

        assert result is False
        db.delete.assert_not_called()
