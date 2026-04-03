import base64
import io
import json
import logging
import re

logger = logging.getLogger(__name__)


class PdfService:
    @staticmethod
    def _replace_plotly_with_images(html_content: str) -> str:
        """
        Substitui divs interativos do Plotly por imagens PNG estáticas.
        WeasyPrint não executa JavaScript, então os gráficos ficariam em branco.
        Extrai o JSON da figura de cada Plotly.newPlot(...) e usa kaleido para gerar PNG.
        """
        try:
            import plotly.io as pio

            decoder = json.JSONDecoder()

            # 1) Encontrar todos os IDs de gráficos Plotly e seus dados
            newplot_pattern = re.compile(
                r"Plotly\.newPlot\(\s*['\"]([^'\"]+)['\"]\s*,\s*",
                re.DOTALL,
            )
            replacements: dict[str, str] = {}  # div_id → <img ...>

            for m in newplot_pattern.finditer(html_content):
                div_id = m.group(1)
                json_start = m.end()
                rest = html_content[json_start:]

                try:
                    first_arg, end_idx = decoder.raw_decode(rest)
                except json.JSONDecodeError:
                    continue

                if isinstance(first_arg, list):
                    # Formato: newPlot(id, [traces], layout, config)
                    traces = first_arg
                    after_traces = rest[end_idx:]
                    comma = re.match(r"\s*,\s*", after_traces)
                    if comma:
                        try:
                            layout, _ = decoder.raw_decode(after_traces[comma.end():])
                        except json.JSONDecodeError:
                            layout = {}
                    else:
                        layout = {}
                    figure_dict = {"data": traces, "layout": layout}
                elif isinstance(first_arg, dict):
                    # Formato: newPlot(id, {data, layout, ...})
                    figure_dict = first_arg
                else:
                    continue

                try:
                    fig = pio.from_json(json.dumps(figure_dict))
                    img_bytes = fig.to_image(format="png", scale=2)
                    b64 = base64.b64encode(img_bytes).decode()
                    w = (figure_dict.get("layout") or {}).get("width", 800)
                    h = (figure_dict.get("layout") or {}).get("height", 400)
                    replacements[div_id] = (
                        f'<img src="data:image/png;base64,{b64}" '
                        f'style="width:{w}px;height:{h}px;max-width:100%;" />'
                    )
                except Exception as exc:
                    logger.warning("Falha ao renderizar gráfico '%s': %s", div_id, exc)

            if not replacements:
                return html_content

            result = html_content

            # 2) Substituir cada <div id="ID" class="plotly-graph-div"...>...</div>
            for div_id, img_tag in replacements.items():
                # Div vazio do gráfico
                div_pat = re.compile(
                    rf'<div\s[^>]*id="{re.escape(div_id)}"[^>]*class="plotly-graph-div"[^>]*>[\s\S]*?</div>',
                    re.DOTALL,
                )
                result = div_pat.sub(img_tag, result)

                # Remover o bloco <script> que contém o Plotly.newPlot deste ID
                script_pat = re.compile(
                    rf'<script[^>]*>[\s\S]*?Plotly\.newPlot\(\s*[\'"]{re.escape(div_id)}[\'"][\s\S]*?</script>',
                    re.DOTALL,
                )
                result = script_pat.sub("", result)

            return result

        except Exception as exc:
            logger.warning("_replace_plotly_with_images falhou (usando HTML original): %s", exc)
            return html_content

    @staticmethod
    def html_to_pdf(html_content: str, base_url: str | None = None) -> bytes:
        """Converte HTML para PDF usando WeasyPrint. Substitui gráficos Plotly por PNGs estáticos."""
        try:
            from weasyprint import HTML  # lazy import — opcional em desenvolvimento

            processed = PdfService._replace_plotly_with_images(html_content)
            buffer = io.BytesIO()
            HTML(string=processed, base_url=base_url).write_pdf(buffer)
            return buffer.getvalue()
        except Exception as e:
            logger.error("Erro ao converter HTML para PDF: %s", e)
            raise RuntimeError(f"Falha na conversão PDF: {e}") from e
