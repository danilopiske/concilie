
import { apiClient } from './client';

export interface AbusividadeItem {
  data_venda: string;
  cod_autorizacao: string;
  horario: string;
  valor_venda: number;
  taxa_aplicada: number;
  numero_maquina: string;
  bandeira: string;
  forma_pagamento: string;
  chave_agrupamento: string;
}

export const abusividadeApi = {
  getAnalise: async (processamentoId: string, agrupamento: string = 'dia', tolerancia: number = 0) => {
    const { data } = await apiClient.get<AbusividadeItem[]>(`abusividade/analise/${encodeURIComponent(processamentoId)}?agrupamento=${agrupamento}&tolerancia=${tolerancia}`);
    return data;
  },

  getRelatorio: async (params: {
    cliente_id: number;
    ec_id?: string;
    data_ini: string;
    data_fim: string;
    agrupamento: string;
  }) => {
    const query = new URLSearchParams({
      cliente_id: params.cliente_id.toString(),
      data_ini: params.data_ini,
      data_fim: params.data_fim,
      agrupamento: params.agrupamento,
    });

    if (params.ec_id) query.append('ec_id', params.ec_id);

    const { data } = await apiClient.get<AbusividadeItem[]>(`abusividade/relatorio?${query.toString()}`);
    return data;
  }
};
