import { apiClient } from './client';

export interface CalculoPreviewRequest {
  processamento_id: string;
  tipo_taxa: string;
  usar_taxa_cad: boolean;
  tem_receba_rapido: boolean;
}

export interface CalculoStats {
  total_vendas: number;
  valor_total: number;
  valor_medio: number;
  min_taxa_orig: number;
  max_taxa_orig: number;
  media_taxa_orig: number;
  vendas_com_cad: number;
  vendas_com_log: number;
  taxas_rr_count: number;
}

export interface CalculoResultado {
  id: number;
  id_venda: number;
  data_venda: string;
  bandeira: string;
  forma_pagamento: string;
  vl_venda: number;
  tx_venda: number;
  tx_calc?: number;
  diff_taxa?: number;
  perda?: number;
}

export const calculoApi = {
  preview: async (req: CalculoPreviewRequest): Promise<CalculoStats> => {
    const response = await apiClient.post<CalculoStats>('/calculos/preview', req);
    return response.data;
  },

  processar: async (req: CalculoPreviewRequest): Promise<void> => {
    await apiClient.post('/calculos/processar', req);
  },

  listarResultados: async (calcId: string, skip = 0, limit = 100): Promise<CalculoResultado[]> => {
    const response = await apiClient.get<CalculoResultado[]>(`/calculos/resultados/${calcId}`, {
      params: { skip, limit }
    });
    return response.data;
  }
};
