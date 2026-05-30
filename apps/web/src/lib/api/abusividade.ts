
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

export interface GranularidadeItem {
  label: string;
  taxa_media: number;
  quantidade: number;
  variacao_vs_media: number;
  status: 'normal' | 'atencao' | 'critico';
}

export interface BandeiraFormaPagamento {
  bandeira: string;
  forma_pagamento: string;
  taxa_media_geral: number;
  por_dia_semana: GranularidadeItem[];
  por_hora: GranularidadeItem[];
  por_semana_mes: GranularidadeItem[];
}

export interface AbusividadeDetalhadaResponse {
  processamento_id: string;
  total_transacoes: number;
  grupos: BandeiraFormaPagamento[];
}

export interface AbusividadeTaskResponse {
  id: string;
  processamento_id: string;
  status: 'pending' | 'ready' | 'error';
  result_path?: string;
  error_message?: string;
  created_at: string;
}

export interface AbusividadeHistoricoItem {
  id: string;
  processamento_id: string;
  status: 'pending' | 'ready' | 'error';
  result_path?: string;
  error_message?: string;
  created_at: string;
  nome_arquivo?: string;
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
  },

  analisarDetalhado: async (processamentoId: string): Promise<AbusividadeDetalhadaResponse> => {
    const { data } = await apiClient.get<AbusividadeDetalhadaResponse>(
      `abusividade/analise-detalhada/${encodeURIComponent(processamentoId)}`
    );
    return data;
  },

  gerarRelatorio: async (processamentoId: string): Promise<{ task_id: string; status: string }> => {
    const { data } = await apiClient.post(`abusividade/gerar-relatorio`, {
      processamento_id: processamentoId,
      incluir_editor: true,
    });
    return data;
  },

  getTask: async (taskId: string): Promise<AbusividadeTaskResponse> => {
    const { data } = await apiClient.get<AbusividadeTaskResponse>(`abusividade/tasks/${taskId}`);
    return data;
  },

  saveEdit: async (taskId: string, htmlContent: string): Promise<{ success: boolean; path: string }> => {
    const { data } = await apiClient.post(`abusividade/tasks/${taskId}/save-edit`, { html_content: htmlContent });
    return data;
  },

  downloadUrl: (taskId: string): string => {
    const base = apiClient.defaults.baseURL ?? '';
    return `${base}/abusividade/tasks/${taskId}/download`;
  },

  getHistorico: async (clienteId: number): Promise<AbusividadeHistoricoItem[]> => {
    const { data } = await apiClient.get<AbusividadeHistoricoItem[]>(`abusividade/historico/${clienteId}`);
    return data;
  },
};
