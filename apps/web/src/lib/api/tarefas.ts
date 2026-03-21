import { apiClient } from './client';

export interface TarefaItem {
  id: string;
  status: string;
  created_at: string;
  usuario?: string;
  progress?: number;
}

export interface TarefasResumo {
  importacoes: TarefaItem[];
  calculos: TarefaItem[];
  relatorios: TarefaItem[];
  abusividades: TarefaItem[];
}

export const tarefasApi = {
  getResumo: async (): Promise<TarefasResumo> => {
    const response = await apiClient.get<TarefasResumo>('/tarefas/resumo');
    return response.data;
  },
};
