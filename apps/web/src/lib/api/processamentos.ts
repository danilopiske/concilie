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

export const processamentosApi = {
  getDetalhes: async (processamentoId: string): Promise<ProcessamentoDetalhes> => {
    const response = await apiClient.get<ProcessamentoDetalhes>(
      `/processamentos/${processamentoId}/detalhes`
    );
    return response.data;
  },
};
