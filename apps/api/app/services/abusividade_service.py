
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, text
from datetime import datetime, timedelta
from app.models.vendas_calculos import VendasCalculos

class AbusividadeService:
    def __init__(self, db: Session):
        self.db = db

    def analisar_processamento(self, processamento_id: str, agrupamento: str = 'hierarquico') -> List[Dict[str, Any]]:
        """
        Analisa um processamento específico em busca de variações de taxa.
        Padrão: 'hierarquico' (Dia > 3Dias > Semana > Mes).
        """
        if agrupamento == 'hierarquico':
            return self._analisar_hierarquia(processamento_id)
        return self._detectar_variacoes(processamento_id=processamento_id, agrupamento=agrupamento)

    def _analisar_hierarquia(self, processamento_id: str) -> List[Dict[str, Any]]:
        niveis = ['dia', '3dias', 'semana', 'mes']
        todos_resultados = []
        ids_processados = set()

        for nivel in niveis:
            resultados = self._detectar_variacoes(processamento_id=processamento_id, agrupamento=nivel)
            
            novos_resultados = []
            for item in resultados:
                if item['id'] not in ids_processados:
                    # Marca como processado
                    ids_processados.add(item['id'])
                    
                    # Adiciona tag do nível no display da chave (opcional, mas bom pra debug/visual)
                    # Mas a chave_agrupamento precisa manter consistencia para o front agrupar.
                    # Vamos injetar um campo 'nivel_analise' ou modificar a chave.
                    # O front agrupa por 'chave_agrupamento'. Se eu mudar a chave, cria grupos separados.
                    # Isso é BOM. Queremos ver "Variacao Dia 25" separado de "Variacao Semana X".
                    # As chaves ja sao unicas por nivel (ex: contem 'W5' ou '2025-01-25').
                    
                    novos_resultados.append(item)
            
            todos_resultados.extend(novos_resultados)
        
        # Ordenar tudo por data
        todos_resultados.sort(key=lambda x: x['data_venda'] or datetime.min)
        return todos_resultados

    def gerar_relatorio(
        self, 
        cliente_id: int, 
        ec_id: Optional[str], 
        data_ini: datetime, 
        data_fim: datetime,
        agrupamento: str = 'dia' # dia, semana, mes, periodo_total
    ) -> List[Dict[str, Any]]:
        """
        Gera relatório de abusividade baseado em filtros.
        """
        return self._detectar_variacoes(
            cliente_id=cliente_id,
            ec_id=ec_id,
            data_ini=data_ini,
            data_fim=data_fim,
            agrupamento=agrupamento
        )

    def _detectar_variacoes(
        self,
        processamento_id: Optional[str] = None,
        cliente_id: Optional[int] = None,
        ec_id: Optional[str] = None,
        data_ini: Optional[datetime] = None,
        data_fim: Optional[datetime] = None,
        agrupamento: str = 'periodo_total'
    ) -> List[Dict[str, Any]]:
        """
        Núcleo da lógica de detecção de variação.
        1. Filtra as vendas (Calculos).
        2. Agrupa por Bandeira + Forma Pagamento (+ Periodo se necessário).
        3. Identifica grupos com count(distinct tx_venda) > 1.
        4. Retorna as transações detalhadas desses grupos.
        """
        
        # Base query
        query = self.db.query(VendasCalculos)

        if processamento_id:
            query = query.filter(VendasCalculos.calc_id == str(processamento_id))
        
        # Filtros adicionais (se não for por processamento direto, ou em adição)
        if ec_id:
             query = query.filter(VendasCalculos.ec_id == ec_id)
        
        if data_ini:
             query = query.filter(VendasCalculos.data_venda >= data_ini)
        
        if data_fim:
             query = query.filter(VendasCalculos.data_venda <= data_fim)

        # Como VendasCalculos não tem cliente_id direto facil (tem id_venda), 
        # assumimos que o filtro de EC + Datas ou Processamento é suficiente.
        # Se precisar de cliente_id, teríamos que fazer join com VendasProcessadas 
        # ou confiar que o EC pertence ao cliente.
        
        vendas = query.all()
        
        # Processamento em Memória (Pandas seria melhor pra volume, mas SQL puro é complexo para "retornar detalhes")
        # Vamos agrupar em dicionário
        
        # Chave de Agrupamento: Bandeira | FormaPagamento | (Periodo)
        grupos: Dict[str, List[VendasCalculos]] = {}

        for v in vendas:
            key = f"{v.bandeira}|{v.forma_pagamento}"
            
            # Se agrupamento não for 'periodo_total' e nem processamento unico,
            # teríamos que granularizar a chave.
            # O pedido diz: "VARIACAO DENTRO DE UM MESMO DIA, OU 3 DIAS, OU 1 SEMANA..."
            # Isso implica que se eu escolho "DIA", eu verifico se NO DIA X houve variacao.
            
            if agrupamento == 'dia':
                key += f"|{v.data_venda.strftime('%Y-%m-%d')}"
            elif agrupamento == '3dias':
                # Agrupa a cada 3 dias fixos (ordinal // 3)
                block = v.data_venda.toordinal() // 3
                key += f"|Block3D-{block}"
            elif agrupamento == 'semana':
                # Agrupa por Ano + Numero da Semana
                iso_calendar = v.data_venda.isocalendar()
                key += f"|W{iso_calendar[1]}-{iso_calendar[0]}"
            elif agrupamento == 'mes':
                key += f"|{v.data_venda.strftime('%Y-%m')}"
            
            if key not in grupos:
                grupos[key] = []
            grupos[key].append(v)
            
        # Analisar Desvios
        resultados = []

        for key, lista in grupos.items():
            # Coletar taxas distintas
            # Converter para float para evitar issues de decimal precision sutil
            taxas = set()
            for v in lista:
                if v.tx_venda is not None:
                    taxas.add(float(v.tx_venda))
            
            if len(taxas) > 1:
                # EUREKA: Tem variação!
                # Adicionar todas as transações desse grupo ao resultado
                for v in lista:
                    resultados.append({
                        "id": v.id, # ID unico para controle de duplicidade hierarquica
                        "data_venda": v.data_venda,
                        "cod_autorizacao": v.cod_autorizacao or v.nsu or "N/A", # Fallback
                        "horario": v.data_venda.strftime("%H:%M:%S") if v.data_venda else "--",
                        "valor_venda": float(v.vl_venda) if v.vl_venda else 0.0,
                        "taxa_aplicada": float(v.tx_venda) if v.tx_venda else 0.0,
                        "numero_maquina": v.ec_id, # Placeholder conforme combinado
                        "bandeira": v.bandeira,
                        "forma_pagamento": v.forma_pagamento,
                        "chave_agrupamento": key
                    })

        # Ordenar por data
        resultados.sort(key=lambda x: x['data_venda'] or datetime.min)
        
        return resultados
