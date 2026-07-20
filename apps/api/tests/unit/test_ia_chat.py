"""Testes unitários para AIService.chat e check_rate_limit."""
from unittest.mock import MagicMock, patch

import pytest

from app.services.ai_service import AIService, check_rate_limit


# ---------------------------------------------------------------------------
# check_rate_limit
# ---------------------------------------------------------------------------

def test_rate_limit_permite_dentro_do_limite():
    user_id = "test_user_rate_ok"
    for _ in range(10):
        assert check_rate_limit(user_id, max_per_minute=10) is True


def test_rate_limit_bloqueia_apos_limite():
    user_id = "test_user_rate_block"
    for _ in range(10):
        check_rate_limit(user_id, max_per_minute=10)
    assert check_rate_limit(user_id, max_per_minute=10) is False


# ---------------------------------------------------------------------------
# AIService.chat — mock do google.generativeai
# ---------------------------------------------------------------------------

RESPOSTA_GEMINI = (
    "A bandeira Visa Crédito apresentou o maior desvio de taxa.\n"
    '{"sugestoes": ["Qual o valor total de perda?", "Quais períodos foram afetados?", "Houve contestação?"]}'
)


@patch("app.services.ai_service.settings")
def test_chat_sem_gemini_key_retorna_mensagem_config(mock_settings):
    mock_settings.GEMINI_API_KEY = ""
    service = AIService.__new__(AIService)
    resposta, sugestoes = service.chat("pergunta", "contexto", [])
    assert "GEMINI_API_KEY" in resposta
    assert sugestoes == []


@patch("app.services.ai_service.settings")
def test_chat_extrai_sugestoes_do_json(mock_settings):
    mock_settings.GEMINI_API_KEY = "fake-key"
    mock_settings.GEMINI_MODEL = "gemini-2.0-flash"

    mock_response = MagicMock()
    mock_response.text = RESPOSTA_GEMINI

    mock_chat = MagicMock()
    mock_chat.send_message.return_value = mock_response

    mock_model = MagicMock()
    mock_model.start_chat.return_value = mock_chat

    with patch.dict("sys.modules", {"google.generativeai": MagicMock()}):
        import google.generativeai as genai  # noqa: F401
        with patch("google.generativeai.configure"), \
             patch("google.generativeai.GenerativeModel", return_value=mock_model):
            service = AIService.__new__(AIService)
            resposta, sugestoes = service.chat("pergunta", "contexto", [])

    assert "sugestoes" not in resposta  # JSON removido do texto
    assert len(sugestoes) == 3
    assert sugestoes[0] == "Qual o valor total de perda?"


def test_montar_contexto_sem_dados_retorna_mensagem_vazia():
    db = MagicMock()
    db.query.return_value.filter.return_value.all.return_value = []
    service = AIService.__new__(AIService)
    contexto, dados = service.montar_contexto("proc-inexistente", db)
    assert "Nenhum dado encontrado" in contexto
    assert dados == {}
