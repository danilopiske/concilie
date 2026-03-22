import logging
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from app.services.abusividade_service import AbusividadeService

logger = logging.getLogger(__name__)


class AbusividadeRelatorioService:
    def __init__(self, db: Session):
        self.db = db
        self.output_dir = "relatorios_gerados"
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir, exist_ok=True)

    def gerar_html(self, processamento_id: str, data_inicio=None, data_fim=None) -> str:
        # --- SAFE INITIALIZATION ---
        dados: List[Dict[str, Any]] = []
        rows_list: List[str] = []
        cnpj_placeholder = "07.464.624/0001-09"
        adquirente_placeholder = "N/A"

        logger.info(
            "Iniciando cálculo abusividade processamento_id=%s período=%s..%s",
            processamento_id,
            data_inicio,
            data_fim,
        )
        _t0 = time.monotonic()

        try:
            service = AbusividadeService(self.db)
            # Fetch data from optimized Polars-based service
            dados = service.analisar_processamento(processamento_id)

            # Filter by dates if provided
            if data_inicio:
                dados = [d for d in dados if d['data_venda'] >= data_inicio]
            if data_fim:
                dados = [d for d in dados if d['data_venda'] <= data_fim]

            if not dados:
                return None

            adquirente_placeholder = dados[0]['bandeira'] if dados else "N/A"

            # Efficient row building using list and join
            for d in dados:
                data_str = d['data_venda'].strftime('%d/%m/%Y') if d['data_venda'] else '-'
                valor_str = f"R$ {d['valor_venda']:.2f}"
                taxa_str = f"{d['taxa_aplicada']:.2f}%"

                rows_list.append(f"""
                <tr>
                    <td>{data_str}</td>
                    <td>{d['cod_autorizacao']}</td>
                    <td>{d['horario']}</td>
                    <td>{valor_str}</td>
                    <td class="rate">{taxa_str}</td>
                    <td>{d['numero_maquina']}</td>
                    <td>{d['bandeira']}</td>
                </tr>""")

            formatted_rows = "".join(rows_list)
            num_dias = len(set(d['data_venda'].date() for d in dados if d['data_venda']))

            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <title>Demonstrativo de Oscilações</title>
                <style>
                    body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 40px; color: #333; background-color: #f9f9f9; }}
                    .container {{ background: #fff; padding: 40px; border-radius: 8px; box-shadow: 0 4px 15px rgba(0,0,0,0.1); max-width: 1000px; margin: auto; }}
                    h1 {{ text-align: center; color: #2c3e50; font-size: 26px; margin-bottom: 20px; border-bottom: 2px solid #3498db; padding-bottom: 15px; }}
                    .header-info {{ text-align: center; margin-bottom: 40px; font-size: 15px; color: #7f8c8d; }}
                    .content {{ margin-bottom: 40px; line-height: 1.8; text-align: justify; font-size: 16px; }}
                    table {{ width: 100%; border-collapse: collapse; margin-top: 25px; font-size: 13px; background: white; }}
                    th, td {{ border: 1px solid #eee; padding: 12px 8px; text-align: center; }}
                    th {{ background-color: #3498db; color: white; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px; }}
                    tr:nth-child(even) {{ background-color: #f2f6f9; }}
                    tr:hover {{ background-color: #e1f0fa; transition: 0.2s; }}
                    .rate {{ color: #e74c3c; font-weight: bold; }}
                    .highlight {{ background-color: #fff3cd; color: #856404; padding: 2px 6px; border-radius: 4px; font-weight: bold; }}
                    .text-bold {{ font-weight: bold; color: #2c3e50; }}
                    .footer-note {{ margin-top: 30px; font-size: 12px; color: #95a5a6; text-align: center; font-style: italic; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <h1>Demonstrativo de Oscilações na Aplicação de Taxas</h1>

                    <div class="header-info">
                        <p><strong>CNPJ:</strong> {cnpj_placeholder}</p>
                        <p><strong>Adquirente:</strong> {adquirente_placeholder}</p>
                    </div>

                    <div class="content">
                        <p>Abaixo, apresentamos a demonstração detalhada das variações identificadas nos extratos eletrônicos,
                        fundamentada em auditoria sistêmica tecnicamente especializada.</p>

                        <p>Constatou-se que, <span class="text-bold" style="text-decoration: underline;">em apenas {num_dias} dias de faturamento</span>, a Adquirente aplicou
                        <span class="highlight">taxas diferentes</span> sobre a mesma bandeira e modalidade para a adquirente {adquirente_placeholder},
                        evidenciando falta de padronização e impacto financeiro direto ao estabelecimento:</p>
                    </div>

                    <table>
                        <thead>
                            <tr>
                                <th>DATA</th>
                                <th>CÓDIGO AUTORIZAÇÃO</th>
                                <th>HORÁRIO</th>
                                <th>VALOR</th>
                                <th>TAXA DESCONTADA</th>
                                <th>Nº MÁQUINA (EC)</th>
                                <th>BANDEIRA</th>
                            </tr>
                        </thead>
                        <tbody>
                            {formatted_rows}
                        </tbody>
                    </table>

                    <div class="footer-note">
                        Relatório gerado em {datetime.now().strftime('%d/%m/%Y %H:%M:%S')} - Auditoria Concilie
                    </div>
                </div>
            </body>
            </html>
            """

            filename = f"Demonstrativo_Abusividade_{processamento_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}.html"
            full_path = os.path.join(self.output_dir, filename)

            with open(full_path, "w", encoding="utf-8") as f:
                f.write(html_content)

            elapsed = time.monotonic() - _t0
            logger.info(
                "Concluído processamento_id=%s linhas=%d tempo=%.2fs",
                processamento_id,
                len(dados),
                elapsed,
            )
            return full_path

        except Exception as e:
            logger.exception(
                "Erro ao gerar relatório de abusividade processamento_id=%s",
                processamento_id,
            )
            return None

    def gerar_relatorio_async(self, task_id: str, processamento_id: str, db: Session) -> None:
        """Gera HTML de abusividade com editor-appendix e salva em relatorios_cache/abusividade/."""
        from app.models.abusividade_task import AbusividadeTask

        logger.info("gerar_relatorio_async task_id=%s processamento_id=%s", task_id, processamento_id)
        task = db.query(AbusividadeTask).filter(AbusividadeTask.id == task_id).first()
        if not task:
            logger.error("AbusividadeTask não encontrada task_id=%s", task_id)
            return

        try:
            html_path = self.gerar_html(processamento_id)
            if not html_path:
                task.status = "error"
                task.error_message = "Nenhuma variação de taxa encontrada para este processamento."
                db.commit()
                return

            with open(html_path, "r", encoding="utf-8") as f:
                html_content = f.read()

            editor_section = '<section class="editor-appendix"></section>'
            html_content = html_content.replace("</body>", f"{editor_section}\n</body>")

            cache_dir = Path("relatorios_cache/abusividade")
            cache_dir.mkdir(parents=True, exist_ok=True)
            dest = cache_dir / f"{task_id}.html"
            with open(dest, "w", encoding="utf-8") as f:
                f.write(html_content)

            task.status = "ready"
            task.result_path = str(dest)
            db.commit()
            logger.info("Relatório async concluído task_id=%s path=%s", task_id, dest)

            # Notificação de abusividade detectada (não-bloqueante)
            try:
                from app.services.notificacao_service import NotificacaoService
                NotificacaoService.criar(
                    db,
                    tipo="abusividade_detectada",
                    titulo="Abusividade detectada",
                    mensagem=f"Demonstrativo de oscilações gerado para o processamento {processamento_id}.",
                    link="/abusividade",
                )
            except Exception:
                pass

        except Exception as e:
            logger.exception("Erro no gerar_relatorio_async task_id=%s", task_id)
            task.status = "error"
            task.error_message = str(e)[:500]
            db.commit()

