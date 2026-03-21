import { apiClient } from './client';

export interface ProcessamentoTaskItem {
  id: string;
  status: string;
  created_at: string;
  usuario?: string;
  progress?: number;
  tipo_relatorio?: string;
  result_path?: string;
}

export interface ProcessamentoDetalhes {
  processamento_id: string;
  status_geral: 'concluido' | 'em_andamento' | 'com_erro' | 'parcial' | 'sem_dados';
  totais: {
    importacoes: number;
    calculos: number;
    relatorios: number;
    abusividades: number;
  };
  importacoes: ProcessamentoTaskItem[];
  calculos: ProcessamentoTaskItem[];
  relatorios: ProcessamentoTaskItem[];
  abusividades: ProcessamentoTaskItem[];
}

export interface ProcessamentoListParams {
  cliente_id?: number;
  periodo?: number;
  status?: string;
  skip?: number;
  limit?: number;
  simple?: boolean;
}

export const processamentosApi = {
  getDetalhes: async (processamentoId: string): Promise<ProcessamentoDetalhes> => {
    const response = await apiClient.get<ProcessamentoDetalhes>(
      `/processamentos/${processamentoId}/detalhes`
    );
    return response.data;
  },

  listar: async (params?: ProcessamentoListParams) => {
    const response = await apiClient.get('/processamentos/', { params });
    return response.data;
  },

  exportarCsvUrl: (params?: { cliente_id?: number; periodo?: number }): string => {
    const baseUrl = (apiClient.defaults.baseURL ?? '').replace(/\/$/, '');
    const qs = new URLSearchParams();
    if (params?.cliente_id) qs.set('cliente_id', String(params.cliente_id));
    if (params?.periodo) qs.set('periodo', String(params.periodo));
    const query = qs.toString();
    return `${baseUrl}/processamentos/exportar-csv${query ? `?${query}` : ''}`;
  },
};
