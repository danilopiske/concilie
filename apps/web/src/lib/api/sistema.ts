import { apiClient } from './client';

export interface SistemaStatus {
  api: string;
  database: string;
  metricas: {
    total_clientes: number;
    total_importacoes: number;
    total_calculos: number;
    total_relatorios: number;
    tarefas_ativas: number;
  };
  ultimas_tarefas: {
    importacoes: Array<{ id: string; status: string; created_at: string }>;
    calculos: Array<{ id: string; status: string; created_at: string }>;
    relatorios: Array<{ id: string; status: string; created_at: string }>;
  };
}

export const sistemaApi = {
  getStatus: async (): Promise<SistemaStatus> => {
    const response = await apiClient.get<SistemaStatus>('/sistema/status');
    return response.data;
  },
};
