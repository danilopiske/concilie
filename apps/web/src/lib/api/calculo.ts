import { apiClient } from './client';

export interface CalculoPreviewRequest {
  processamento_id: string;
  tipo_taxa: string;
  usar_taxa_cad: boolean;
  tem_receba_rapido: boolean;
  substituir?: boolean;
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
  calc_id: string;
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

export interface CalculoHistoryItem {
  calc_id: string;
  calc_tipo: string;
  calc_usuario: string;
  calc_data: string;
  total_registros: number;
  total_valor: number;
  perda_total: number;
}

export interface CalculoTask {
  id: string;
  status: 'PENDING' | 'PROCESSING' | 'SUCCESS' | 'FAILED';
  progress: number;
  message: string;
  updated_at: string;
  processamento_id: number;
  tipo_taxa: string;
}

export interface PeriodoAnalise {
  periodo: string;
  quantidade: number;
  valor_total: number;
  status: 'ok' | 'reduzido' | 'ausente';
}

export interface AnalisePeriodosResponse {
  processamento_id: string;
  total_periodos: number;
  periodos_ausentes: number;
  periodos_reduzidos: number;
  mediana_quantidade: number;
  periodos: PeriodoAnalise[];
}

export const calculoApi = {
  preview: async (req: CalculoPreviewRequest): Promise<CalculoStats> => {
    const response = await apiClient.post<CalculoStats>('calculos/preview', req);
    return response.data;
  },

  processar: async (req: CalculoPreviewRequest): Promise<void> => {
    await apiClient.post('calculos/processar', req);
  },

  processarAsync: async (req: CalculoPreviewRequest): Promise<{ task_id: string }> => {
    const response = await apiClient.post<{ task_id: string }>('calculos/processar-async', req);
    return response.data;
  },

  getTaskStatus: async (taskId: string): Promise<CalculoTask> => {
    const response = await apiClient.get<CalculoTask>(`calculos/task/${taskId}`);
    return response.data;
  },

  listarResultados: async (calcId: string, skip = 0, limit = 100): Promise<CalculoResultado[]> => {
    const response = await apiClient.get<CalculoResultado[]>(`calculos/resultados/${calcId}`, {
      params: { skip, limit }
    });
    return response.data;
  },

  getHistory: async (skip = 0, limit = 50): Promise<CalculoHistoryItem[]> => {
    const response = await apiClient.get<CalculoHistoryItem[]>('calculos/historico-calculos', {
      params: { skip, limit }
    });
    return response.data;
  },

  deleteCalculo: async (calcId: string): Promise<void> => {
    await apiClient.delete(`calculos/deletar/${calcId}`);
  },

  analisePeriodos: async (processamentoId: string, threshold = 0.5): Promise<AnalisePeriodosResponse> => {
    const response = await apiClient.get<AnalisePeriodosResponse>(
      `calculos/analise-periodos/${processamentoId}`,
      { params: { threshold } }
    );
    return response.data;
  },

  exportExcel: (calcId: string): void => {
    const token = typeof window !== 'undefined' ? localStorage.getItem('access_token') : null;
    const baseUrl = apiClient.defaults.baseURL;
    const url = `${baseUrl}/calculos/export/${encodeURIComponent(calcId)}`;

    // Fetch com auth header e disparar download via blob
    fetch(url, {
      credentials: 'include',
      headers: token ? { Authorization: `Bearer ${token}` } : {},
    })
      .then((res) => {
        if (!res.ok) throw new Error('Erro ao exportar Excel');
        return res.blob();
      })
      .then((blob) => {
        const link = document.createElement('a');
        link.href = URL.createObjectURL(blob);
        link.download = `calculo_${calcId}.xlsx`;
        link.click();
        URL.revokeObjectURL(link.href);
      })
      .catch((err) => console.error(err));
  },
};
