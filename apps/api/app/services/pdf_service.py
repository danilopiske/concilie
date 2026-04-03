import base64
import io
import json
import logging
import re

logger = logging.getLogger(__name__)


class PdfService:
    @staticmethod
    def _render_all_figures(figure_dicts: list[tuple[str, dict]], total_timeout_s: int = 60) -> dict[str, bytes]:
        """
        Converte uma lista de figuras Plotly para PNG usando kaleido.
        Usa um único executor com timeout global para evitar que o subprocess
        de chromium fique pendurado indefinidamente.
        Retorna dict {div_id: png_bytes}. IDs que falharam são omitidos.
        """
        import concurrent.futures
        import plotly.io as pio

        results: dict[str, bytes] = {}
        if not figure_dicts:
            return results

        def _render_one(div_id: str, figure_dict: dict) -> tuple[str, bytes | None]:
            try:
                fig = pio.from_json(json.dumps(figure_dict))
                img = fig.to_image(format="png", scale=2)
                return div_id, img
            except Exception as exc:
                logger.warning("[PDF] Falha ao renderizar gráfico '%s': %s", div_id, exc)
                return div_id, None

        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
            futures = {executor.submit(_render_one, did, fd): did for did, fd in figure_dicts}
            done, not_done = concurrent.futures.wait(
                futures, timeout=total_timeout_s, return_when=concurrent.futures.ALL_COMPLETED
            )
            if not_done:
                logger.warning(
                    "[PDF] Timeout global (%ds) — %d gráfico(s) não renderizados",
                    total_timeout_s, len(not_done),
                )
            for f in done:
                div_id, img = f.result()
                if img:
                    results[div_id] = img

        return results

    @staticmethod
    def _replace_plotly_with_images(html_content: str) -> str:
        """
        Substitui divs interativos do Plotly por imagens PNG estáticas.
        WeasyPrint não executa JavaScript, então os gráficos ficariam em branco.
        Extrai o JSON da figura de cada Plotly.newPlot(...) e usa kaleido para gerar PNG.
        Gráficos que falhem ou excedam 30s de timeout são removidos sem quebrar o PDF.
        """
        try:
            decoder = json.JSONDecoder()

            newplot_pattern = re.compile(
                r"Plotly\.newPlot\(\s*['\"]([^'\"]+)['\"]\s*,\s*",
                re.DOTALL,
            )
            replacements: dict[str, str] = {}  # div_id → <img ...> ou ""

            matches = list(newplot_pattern.finditer(html_content))
            logger.info("[PDF] Encontrados %d gráfico(s) Plotly para converter", len(matches))

            # Fase 1: parsear todos os JSONs das figuras
            figure_dicts: list[tuple[str, dict]] = []
            for m in matches:
                div_id = m.group(1)
                rest = html_content[m.end():]
                try:
                    first_arg, end_idx = decoder.raw_decode(rest)
                except json.JSONDecodeError:
                    logger.warning("[PDF] Falha ao parsear JSON do gráfico '%s'", div_id)
                    replacements[div_id] = ""
                    continue

                if isinstance(first_arg, list):
                    after_traces = rest[end_idx:]
                    comma = re.match(r"\s*,\s*", after_traces)
                    if comma:
                        try:
                            layout, _ = decoder.raw_decode(after_traces[comma.end():])
                        except json.JSONDecodeError:
                            layout = {}
                    else:
                        layout = {}
                    fd = {"data": first_arg, "layout": layout}
                elif isinstance(first_arg, dict):
                    fd = first_arg
                else:
                    replacements[div_id] = ""
                    continue

                figure_dicts.append((div_id, fd))

            # Fase 2: renderizar todos com timeout global de 60s
            rendered = PdfService._render_all_figures(figure_dicts, total_timeout_s=60)

            for div_id, fd in figure_dicts:
                img_bytes = rendered.get(div_id)
                if img_bytes:
                    b64 = base64.b64encode(img_bytes).decode()
                    w = (fd.get("layout") or {}).get("width", 800)
                    h = (fd.get("layout") or {}).get("height", 400)
                    replacements[div_id] = (
                        f'<img src="data:image/png;base64,{b64}" '
                        f'style="width:{w}px;height:{h}px;max-width:100%;" />'
                    )
                else:
                    replacements[div_id] = ""

            if not replacements:
                return html_content

            result = html_content
            for div_id, img_tag in replacements.items():
                div_pat = re.compile(
                    rf'<div\s[^>]*id="{re.escape(div_id)}"[^>]*class="plotly-graph-div"[^>]*>[\s\S]*?</div>',
                    re.DOTALL,
                )
                result = div_pat.sub(img_tag, result)

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
    def html_to_pdf(html_content: str, base_url: str | None = None, skip_charts: bool = False) -> bytes:
        """Converte HTML para PDF usando WeasyPrint. Substitui gráficos Plotly por PNGs estáticos.
        Use skip_charts=True para pular a conversão de gráficos (diagnóstico / fallback)."""
        try:
            from weasyprint import HTML  # lazy import — opcional em desenvolvimento

            processed = html_content if skip_charts else PdfService._replace_plotly_with_images(html_content)
            if skip_charts:
                logger.info("[PDF] Conversão de gráficos pulada (skip_charts=True)")
            buffer = io.BytesIO()
            HTML(string=processed, base_url=base_url).write_pdf(buffer)
            return buffer.getvalue()
        except Exception as e:
            logger.error("Erro ao converter HTML para PDF: %s", e)
            raise RuntimeError(f"Falha na conversão PDF: {e}") from e
