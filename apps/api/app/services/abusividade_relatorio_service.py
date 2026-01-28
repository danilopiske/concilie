
import os
from datetime import datetime
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from app.services.abusividade_service import AbusividadeService

class AbusividadeRelatorioService:
    def __init__(self, db: Session):
        self.db = db
        self.output_dir = "relatorios_gerados" # Matches where legacy reports go presumably, need to confirm or create
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir, exist_ok=True)

    def gerar_html(self, processamento_id: str, data_inicio=None, data_fim=None) -> str:
        service = AbusividadeService(self.db)
        # Get data filtered by processing (and dates if needed/passed)
        # Note: Report generation usually filters by context of the processing or user input dates
        dados = service.analisar_processamento(processamento_id)
        
        # Filter by dates if provided
        if data_inicio:
             dados = [d for d in dados if d['data_venda'] >= data_inicio]
        if data_fim:
             dados = [d for d in dados if d['data_venda'] <= data_fim]

        if not dados:
            return None

        # Template HTML
        # Using a clean, professional inline CSS styling
        
        cnpj_placeholder = "07.464.624/0001-09" # Could fetch from Client if I query Client table
        adquirente_placeholder = dados[0]['bandeira'] if dados else "N/A"
        
        rows = ""
        for d in dados:
             rows += f"""
             <tr>
                 <td>{d['data_venda'].strftime('%d/%m/%Y') if d['data_venda'] else '-'}</td>
                 <td>{d['cod_autorizacao']}</td>
                 <td>{d['horario']}</td>
                 <td>R$ {d['valor_venda']:.2f}</td>
                 <td class="rate">{d['taxa_aplicada']:.2f}%</td>
                 <td>{d['numero_maquina']}</td>
                 <td>{d['bandeira']}</td>
             </tr>
             """

        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>Demonstrativo de Oscilações</title>
            <style>
                body {{ font-family: Helvetica, Arial, sans-serif; margin: 40px; color: #333; }}
                h1 {{ text-align: center; font-size: 24px; margin-bottom: 20px; }}
                .header-info {{ text-align: center; margin-bottom: 40px; font-size: 14px; }}
                .content {{ margin-bottom: 40px; line-height: 1.6; text-align: justify; }}
                table {{ width: 100%; border-collapse: collapse; margin-top: 20px; font-size: 12px; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                th {{ background-color: #f2f2f2; font-weight: bold; text-align: center; }}
                td {{ text-align: center; }}
                .rate {{ color: #d00; font-weight: bold; }}
                .highlight {{ background-color: #ffeb3b; padding: 0 4px; }}
                .text-bold {{ font-weight: bold; }}
            </style>
        </head>
        <body>
            <h1>Demonstrativo de oscilações na aplicação de taxas</h1>
            
            <div class="header-info">
                <p>CNPJ: {cnpj_placeholder}</p>
                <p>Adquirente: {adquirente_placeholder}.</p>
            </div>

            <div class="content">
                <p>De maneira ainda mais prejudicial, apresentamos demonstração detalhada, fundamentada em informações 
                <strong>extraídas diretamente dos extratos</strong>, dados identificados por meio de auditoria sistêmica e tecnicamente especializada.</p>
                
                <p>Constatou-se que, <span class="text-bold" style="text-decoration: underline;">em apenas (X) dias de faturamento</span>, a Adquirente aplicou 
                <span class="highlight text-bold">taxas diferentes</span> sobre a mesma bandeira e modalidade, {adquirente_placeholder}, 
                <span class="text-bold" style="text-decoration: underline;">evidenciando</span> complexidade excessiva, 
                potencial sobreposição de descontos e impacto financeiro relevante ao estabelecimento:</p>
            </div>

            <table>
                <thead>
                    <tr>
                        <th>DATA</th>
                        <th>CÓDIGO AUTORIZAÇÃO<br>DA TRANSAÇÃO</th>
                        <th>HORÁRIO</th>
                        <th>VALOR DA<br>TRANSAÇÃO</th>
                        <th>TAXA<br>DESCONTADA</th>
                        <th>Nº DA<br>MÁQUINA</th>
                        <th>BANDEIRA</th>
                    </tr>
                </thead>
                <tbody>
                    {rows}
                </tbody>
            </table>
        </body>
        </html>
        """
        
        filename = f"Demonstrativo_Abusividade_{processamento_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}.html"
        full_path = os.path.join(self.output_dir, filename)
        
        with open(full_path, "w", encoding="utf-8") as f:
            f.write(html_content)
            
        return full_path
    
