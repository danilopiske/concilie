import pytest

weasyprint = pytest.importorskip("weasyprint", reason="weasyprint não instalado")

from app.services.pdf_service import PdfService


SIMPLE_HTML = """<!DOCTYPE html>
<html><head><meta charset="UTF-8"/><title>Test</title></head>
<body><h1>PDF Test</h1><p>Smoke test para WeasyPrint.</p></body>
</html>"""


def test_html_to_pdf_retorna_bytes_validos():
    result = PdfService.html_to_pdf(SIMPLE_HTML)
    assert isinstance(result, bytes)
    assert len(result) > 0


def test_html_to_pdf_comeca_com_marcador_pdf():
    result = PdfService.html_to_pdf(SIMPLE_HTML)
    assert result[:4] == b"%PDF", f"PDF deve começar com %PDF, mas começou com {result[:4]!r}"


def test_html_to_pdf_com_css_inline():
    html_com_css = """<!DOCTYPE html>
<html><head><style>@media print { body { font-size: 12pt; } }</style></head>
<body><p>Teste com CSS.</p></body></html>"""
    result = PdfService.html_to_pdf(html_com_css)
    assert result[:4] == b"%PDF"
