import io
import logging

logger = logging.getLogger(__name__)


class PdfService:
    @staticmethod
    def html_to_pdf(html_content: str, base_url: str | None = None) -> bytes:
        """Converte HTML para PDF usando WeasyPrint. Retorna bytes do PDF."""
        try:
            from weasyprint import HTML  # lazy import — opcional em desenvolvimento

            buffer = io.BytesIO()
            HTML(string=html_content, base_url=base_url).write_pdf(buffer)
            return buffer.getvalue()
        except Exception as e:
            logger.error("Erro ao converter HTML para PDF: %s", e)
            raise RuntimeError(f"Falha na conversão PDF: {e}") from e
